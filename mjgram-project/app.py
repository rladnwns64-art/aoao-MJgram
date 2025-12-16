from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_cors import CORS
import os
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'mjgram-secret-key-2024')
CORS(app)

# Supabase 설정
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://tyezthbjowdwnhkrxwjz.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR5ZXp0aGJqb3dkd25oa3J4d2p6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQ1MDcwNTQsImV4cCI6MjA1MDA4MzA1NH0.rG8pXDihJCZyIj23vw_k-Ba1_w_')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# GitHub API Token (선택사항)
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')

# ==================== 메인 페이지 ====================
@app.route('/')
def index():
    return send_from_directory('.', 'mjgram_complete.html')

# ==================== API: 이메일 매직 링크 전송 ====================
@app.route('/api/auth/magic-link', methods=['POST'])
def send_magic_link():
    """이메일 매직 링크 전송"""
    data = request.json
    email = data.get('email')
    
    try:
        response = supabase.auth.sign_in_with_otp({
            'email': email,
            'options': {
                'email_redirect_to': request.host_url
            }
        })
        
        return jsonify({
            'success': True,
            'message': '이메일을 확인해주세요! 로그인 링크를 보냈습니다.'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

# ==================== API: 현재 사용자 정보 ====================
@app.route('/api/auth/user', methods=['GET'])
def get_user():
    """현재 로그인한 사용자 정보"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        token = auth_header.replace('Bearer ', '')
        user = supabase.auth.get_user(token)
        
        # users 테이블에서 추가 정보 가져오기
        user_data = supabase.table('users').select('*').eq('id', user.user.id).single().execute()
        
        return jsonify({
            'success': True,
            'user': user_data.data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 401

# ==================== API: 피드 가져오기 ====================
@app.route('/api/posts', methods=['GET'])
def get_posts():
    """게시물 피드 가져오기"""
    try:
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        response = supabase.table('posts')\
            .select('*, users(username, avatar, github_username)')\
            .order('created_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        return jsonify({
            'success': True,
            'posts': response.data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== API: 게시물 생성 ====================
@app.route('/api/posts', methods=['POST'])
def create_post():
    """새 게시물 생성"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        token = auth_header.replace('Bearer ', '')
        user = supabase.auth.get_user(token)
        
        data = request.json
        post_type = data.get('type')
        
        post_data = {
            'user_id': user.user.id,
            'type': post_type,
            'content': data.get('content', ''),
            'likes_count': 0
        }
        
        if post_type == 'image':
            post_data['image_url'] = data.get('image_url')
        elif post_type == 'code':
            post_data['code'] = data.get('code')
            post_data['language'] = data.get('language', 'python')
        elif post_type == 'project':
            post_data['github_repo_url'] = data.get('github_repo_url')
            post_data['tech_stack'] = data.get('tech_stack', '')
            
            # GitHub API로 레포 정보 가져오기
            github_url = data.get('github_repo_url')
            if github_url:
                github_data = get_github_repo_info(github_url)
                post_data['github_data'] = github_data
        
        result = supabase.table('posts').insert(post_data).execute()
        
        return jsonify({
            'success': True,
            'post': result.data[0]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== API: 게시물 삭제 ====================
@app.route('/api/posts/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    """게시물 삭제"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        token = auth_header.replace('Bearer ', '')
        user = supabase.auth.get_user(token)
        
        # 본인의 게시물인지 확인
        post = supabase.table('posts').select('*').eq('id', post_id).single().execute()
        
        if post.data['user_id'] != user.user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        supabase.table('posts').delete().eq('id', post_id).execute()
        
        return jsonify({
            'success': True,
            'message': '게시물이 삭제되었습니다.'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== API: 좋아요 토글 ====================
@app.route('/api/posts/<post_id>/like', methods=['POST'])
def toggle_like(post_id):
    """좋아요 추가/취소"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        token = auth_header.replace('Bearer ', '')
        user = supabase.auth.get_user(token)
        
        # 이미 좋아요 했는지 확인
        existing = supabase.table('likes')\
            .select('*')\
            .eq('post_id', post_id)\
            .eq('user_id', user.user.id)\
            .execute()
        
        if existing.data:
            # 좋아요 취소
            supabase.table('likes')\
                .delete()\
                .eq('post_id', post_id)\
                .eq('user_id', user.user.id)\
                .execute()
            
            # 카운트 감소
            supabase.rpc('decrement_likes', {'post_id': post_id}).execute()
            
            return jsonify({
                'success': True,
                'action': 'unliked'
            })
        else:
            # 좋아요 추가
            supabase.table('likes').insert({
                'post_id': post_id,
                'user_id': user.user.id
            }).execute()
            
            # 카운트 증가
            supabase.rpc('increment_likes', {'post_id': post_id}).execute()
            
            return jsonify({
                'success': True,
                'action': 'liked'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== API: 댓글 가져오기 ====================
@app.route('/api/posts/<post_id>/comments', methods=['GET'])
def get_comments(post_id):
    """게시물의 댓글 가져오기"""
    try:
        comments = supabase.table('comments')\
            .select('*, users(username, avatar)')\
            .eq('post_id', post_id)\
            .order('created_at', desc=False)\
            .execute()
        
        return jsonify({
            'success': True,
            'comments': comments.data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== API: 댓글 추가 ====================
@app.route('/api/posts/<post_id>/comments', methods=['POST'])
def add_comment(post_id):
    """댓글 추가"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        token = auth_header.replace('Bearer ', '')
        user = supabase.auth.get_user(token)
        
        data = request.json
        content = data.get('content')
        
        if not content:
            return jsonify({'success': False, 'error': 'Content required'}), 400
        
        result = supabase.table('comments').insert({
            'post_id': post_id,
            'user_id': user.user.id,
            'content': content
        }).execute()
        
        return jsonify({
            'success': True,
            'comment': result.data[0]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== API: 사용자 프로필 ====================
@app.route('/api/users/<username>', methods=['GET'])
def get_user_profile(username):
    """사용자 프로필 가져오기"""
    try:
        user = supabase.table('users')\
            .select('*')\
            .eq('username', username)\
            .single()\
            .execute()
        
        # 사용자의 게시물
        posts = supabase.table('posts')\
            .select('*')\
            .eq('user_id', user.data['id'])\
            .order('created_at', desc=True)\
            .execute()
        
        # 팔로워/팔로잉 수 (추후 구현)
        followers_count = 0
        following_count = 0
        
        return jsonify({
            'success': True,
            'user': user.data,
            'posts': posts.data,
            'followers_count': followers_count,
            'following_count': following_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404

# ==================== API: 이미지 업로드 ====================
@app.route('/api/upload/image', methods=['POST'])
def upload_image():
    """이미지 업로드"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        token = auth_header.replace('Bearer ', '')
        user = supabase.auth.get_user(token)
        
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # 파일명 생성
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        file_name = f"{datetime.now().timestamp()}_{user.user.id}.{file_ext}"
        file_path = f"{user.user.id}/{file_name}"
        
        # Supabase Storage에 업로드
        supabase.storage.from_('posts').upload(file_path, file.read())
        
        # 공개 URL 가져오기
        public_url = supabase.storage.from_('posts').get_public_url(file_path)
        
        return jsonify({
            'success': True,
            'url': public_url
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== GitHub 연동 ====================
def get_github_repo_info(repo_url):
    """GitHub 레포지토리 정보 가져오기"""
    try:
        # URL에서 owner/repo 추출
        parts = repo_url.replace('https://github.com/', '').split('/')
        owner, repo = parts[0], parts[1]
        
        headers = {}
        if GITHUB_TOKEN:
            headers['Authorization'] = f'token {GITHUB_TOKEN}'
        
        response = requests.get(
            f'https://api.github.com/repos/{owner}/{repo}',
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'name': data['name'],
                'description': data['description'],
                'stars': data['stargazers_count'],
                'forks': data['forks_count'],
                'language': data['language']
            }
    except:
        pass
    return None

# ==================== API: GitHub 레포 정보 ====================
@app.route('/api/github/repo', methods=['POST'])
def get_github_info():
    """GitHub 레포지토리 정보 가져오기"""
    data = request.json
    repo_url = data.get('url')
    
    if not repo_url:
        return jsonify({'success': False, 'error': 'URL required'}), 400
    
    repo_info = get_github_repo_info(repo_url)
    
    if repo_info:
        return jsonify({
            'success': True,
            'data': repo_info
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to fetch repository info'
        }), 404

# ==================== API: 검색 ====================
@app.route('/api/search', methods=['GET'])
def search():
    """게시물/사용자 검색"""
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'all')  # all, posts, users
    
    try:
        results = {
            'posts': [],
            'users': []
        }
        
        if search_type in ['all', 'posts']:
            # 게시물 검색
            posts = supabase.table('posts')\
                .select('*, users(username, avatar)')\
                .ilike('content', f'%{query}%')\
                .order('created_at', desc=True)\
                .limit(10)\
                .execute()
            results['posts'] = posts.data
        
        if search_type in ['all', 'users']:
            # 사용자 검색
            users = supabase.table('users')\
                .select('*')\
                .or_(f'username.ilike.%{query}%,email.ilike.%{query}%')\
                .limit(10)\
                .execute()
            results['users'] = users.data
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== API: 통계 ====================
@app.route('/api/stats', methods=['GET'])
def get_stats():
    """전체 통계"""
    try:
        # 전체 사용자 수
        users_count = supabase.table('users').select('id', count='exact').execute()
        
        # 전체 게시물 수
        posts_count = supabase.table('posts').select('id', count='exact').execute()
        
        # 전체 좋아요 수
        likes_count = supabase.table('likes').select('id', count='exact').execute()
        
        # 전체 댓글 수
        comments_count = supabase.table('comments').select('id', count='exact').execute()
        
        return jsonify({
            'success': True,
            'stats': {
                'users': users_count.count,
                'posts': posts_count.count,
                'likes': likes_count.count,
                'comments': comments_count.count
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== 에러 핸들러 ====================
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

# ==================== 서버 실행 ====================
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True') == 'True'
    app.run(host='0.0.0.0', port=port, debug=debug)
