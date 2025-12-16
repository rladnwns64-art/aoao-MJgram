# MJgram - 코딩 SNS 🚀

Instagram + GitHub 섞은 개발자 SNS 플랫폼

## 주요 기능 ✨

- 📸 **이미지 게시물** - 일상 공유
- 💻 **코드 게시물** - 코드 스니펫 공유 (Syntax Highlighting)
- 🚀 **프로젝트 게시물** - GitHub 레포지토리 연동
- ❤️ **실시간 좋아요** - Supabase Realtime
- 💬 **실시간 댓글** - 새로고침 없이 업데이트
- 🔔 **실시간 알림** - 새 게시물/댓글 알림
- 📧 **매직 링크 로그인** - 비밀번호 없는 로그인

## 기술 스택 🛠️

### Frontend
- HTML5, CSS3, JavaScript (Vanilla)
- SVG 아이콘
- Supabase Realtime

### Backend
- Python 3.10+
- Flask
- Supabase (PostgreSQL + Realtime + Storage + Auth)

### 배포
- Render (Backend)
- Supabase (Database + Storage + Auth)

## 로컬 실행 방법 💻

### 1. 저장소 클론
```bash
git clone <repository-url>
cd mjgram
```

### 2. Python 가상환경 생성
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
```bash
# .env.example을 .env로 복사
cp .env.example .env

# .env 파일에서 Supabase 정보 입력
```

### 5. Supabase 설정
```sql
-- Supabase SQL Editor에서 실행
-- supabase_setup.sql 내용 전체 복붙 후 실행
```

### 6. 서버 실행
```bash
python app.py
```

서버가 http://localhost:5000 에서 실행됩니다!

## Render 배포 방법 🚀

### 1. GitHub에 코드 푸시
```bash
git init
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Render 설정
1. Render Dashboard → New Web Service
2. GitHub 레포지토리 연결
3. 설정:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment Variables**:
     - `SUPABASE_URL`: Supabase URL
     - `SUPABASE_KEY`: Supabase Anon Key
     - `SECRET_KEY`: 랜덤 문자열

### 3. 배포!
- Render가 자동으로 빌드하고 배포합니다
- 배포 완료되면 URL로 접속!

## 파일 구조 📁

```
mjgram/
├── app.py                      # Flask 서버
├── requirements.txt            # Python 패키지
├── Procfile                    # Render 배포 설정
├── .env.example               # 환경 변수 예시
├── mjgram_complete.html       # 프론트엔드 (Single Page)
└── supabase_setup.sql         # Supabase DB 스키마
```

## API 엔드포인트 📡

### 인증
- `POST /api/auth/magic-link` - 매직 링크 전송
- `GET /api/auth/user` - 현재 사용자 정보

### 게시물
- `GET /api/posts` - 피드 가져오기
- `POST /api/posts` - 게시물 생성
- `DELETE /api/posts/:id` - 게시물 삭제
- `POST /api/posts/:id/like` - 좋아요 토글

### 댓글
- `GET /api/posts/:id/comments` - 댓글 가져오기
- `POST /api/posts/:id/comments` - 댓글 추가

### 사용자
- `GET /api/users/:username` - 프로필 가져오기

### 기타
- `POST /api/upload/image` - 이미지 업로드
- `POST /api/github/repo` - GitHub 레포 정보
- `GET /api/search` - 검색
- `GET /api/stats` - 통계

## 실시간 기능 작동 원리 ⚡

Supabase Realtime을 사용하여 PostgreSQL 변경사항을 WebSocket으로 실시간 전송:

```javascript
supabase
  .channel('posts-channel')
  .on('postgres_changes', 
    { event: 'INSERT', table: 'posts' },
    (payload) => {
      // 새 게시물 자동 추가
      addPostToFeed(payload.new);
    }
  )
  .subscribe();
```

## 환경 변수 설명 🔐

- `SUPABASE_URL` - Supabase 프로젝트 URL
- `SUPABASE_KEY` - Supabase Anon/Public Key
- `SECRET_KEY` - Flask 세션 암호화 키
- `DEBUG` - 디버그 모드 (True/False)
- `PORT` - 서버 포트 (기본: 5000)
- `GITHUB_TOKEN` - GitHub API Token (선택)

## 개발 팁 💡

### 실시간 테스트
```bash
# 브라우저 2개 띄우기
- 크롬 일반 모드: localhost:5000
- 크롬 시크릿 모드: localhost:5000

# 한쪽에서 게시물 올리면
# 다른 쪽에서 실시간으로 나타남!
```

### GitHub API Rate Limit 해결
```bash
# GitHub Personal Access Token 생성
# Settings → Developer settings → Personal access tokens
# public_repo 권한만 필요

# .env에 추가
GITHUB_TOKEN=your_github_token_here
```

## 트러블슈팅 🔧

### CORS 에러
```python
# app.py에서 CORS 설정 확인
CORS(app)
```

### Supabase 연결 실패
```bash
# .env 파일 확인
# URL과 Key가 정확한지 확인
```

### 이미지 업로드 실패
```bash
# Supabase Storage Bucket 확인
# Bucket name: posts
# Public: ✅ 체크
```

## 라이선스 📄

MIT License

## 만든 사람 👨‍💻

Made with 💻 by MJ 코딩학원

---

**MJgram** - 개발자들의 코딩 SNS 🚀
