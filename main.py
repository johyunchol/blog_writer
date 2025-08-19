import os
from time import sleep

import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import json


# --- 2. Gemini를 이용한 블로그 글 생성 함수 ---
def generate_post_with_gemini(api_key):
    """Gemini를 통해 오늘자 부동산 뉴스를 검색하고, 이를 바탕으로 블로그 글을 생성합니다."""
    print("Gemini를 통해 뉴스 검색 및 블로그 글 생성을 시작합니다...")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    today_date = datetime.now().strftime('%Y년 %m월 %d일')

    prompt = f"""
    오늘 날짜({today_date})의 최신 부동산 뉴스 기사를 https://m2.land.naver.com/news 에서 오늘 날짜의 기사를 정리하고, 
    검색된 뉴스 기사들의 핵심 내용을 종합하여 현재 부동산 시장의 동향을 분석하는 전문적인 Tistory 블로그 글을 작성해 주세요.
    
    오늘 날짜의 부동산 뉴스는 다음과 같습니다:
    <div class="article" id="article_today" style=""><div class="title_area"><h3 class="title date">2025.08.19. 화요일</h3></div><ul class="news_list"><li class="item">    <a href="https://n.news.naver.com/article/009/0005542945" target="_blank" class="link">        <span class="text">           <span class="title">‘준강남’ 숲세권 대단지 생긴다···‘10억 로또’도 있다는데 [부동산 이기자]</span>            <span class="information">                <span class="source">매일경제</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/009/2025/08/18/0005542945_001_20250818133606386.jpg?type=nf176_176" width="88" height="88" alt="‘준강남’ 숲세권 대단지 생긴다···‘10억 로또’도 있다는데 [부동산 이기자]" loading="lazy" decoding="async"></span>    </a></li><li class="item">    <a href="https://n.news.naver.com/article/029/0002975948" target="_blank" class="link">        <span class="text">           <span class="title">“못 올린 월세는 관리비로”…집세 전가 ‘꼼수’</span>            <span class="information">                <span class="source">디지털타임스</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/029/2025/08/18/0002975948_001_20250818175512641.png?type=nf176_176" width="88" height="88" alt="“못 올린 월세는 관리비로”…집세 전가 ‘꼼수’" loading="lazy" decoding="async"></span>    </a></li><li class="item">    <a href="https://n.news.naver.com/article/215/0001220390" target="_blank" class="link">        <span class="text">           <span class="title">반도체 이어 바이오까지…'삼성 건설'의 시간 온다</span>            <span class="information">                <span class="source">한국경제TV</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/215/2025/08/18/A202508180196_20250818143608634.png?type=nf176_176" width="88" height="88" alt="반도체 이어 바이오까지…'삼성 건설'의 시간 온다" loading="lazy" decoding="async"></span>    </a></li><li class="item">    <a href="https://n.news.naver.com/article/011/0004522229" target="_blank" class="link">        <span class="text">           <span class="title">"초고층 개발로 한남 넘본다"…신흥 부촌으로 뜨는 성수1~4지구 [집슐랭]</span>            <span class="information">                <span class="source">서울경제</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/011/2025/08/18/0004522229_001_20250818230729017.jpg?type=nf176_176" width="88" height="88" alt="&quot;초고층 개발로 한남 넘본다&quot;…신흥 부촌으로 뜨는 성수1~4지구 [집슐랭]" loading="lazy" decoding="async"></span>    </a></li><li class="item">    <a href="https://n.news.naver.com/article/366/0001100872" target="_blank" class="link">        <span class="text">           <span class="title">이달 하순 과천·잠실에 ‘로또 청약’ 나온다…‘신혼희망타운·디에이치·르엘’ 접수</span>            <span class="information">                <span class="source">조선비즈</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/366/2025/08/18/0001100872_001_20250818070107522.jpg?type=nf176_176" width="88" height="88" alt="이달 하순 과천·잠실에 ‘로또 청약’ 나온다…‘신혼희망타운·디에이치·르엘’ 접수" loading="lazy" decoding="async"></span>    </a></li><li class="item">    <a href="https://n.news.naver.com/article/009/0005543347" target="_blank" class="link">        <span class="text">           <span class="title">[단독] 정책대출 퍼주느라 주택기금 ‘40조 증발’...공공임대 지을 돈없어 서민주거 직격탄</span>            <span class="information">                <span class="source">매일경제</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/009/2025/08/18/0005543347_001_20250818183809330.jpg?type=nf176_176" width="88" height="88" alt="[단독] 정책대출 퍼주느라 주택기금 ‘40조 증발’...공공임대 지을 돈없어 서민주거 직격탄" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/018/0006092340" target="_blank" class="link">        <span class="text">           <span class="title">전셋값 폭등에 피할 수 없는 '월세살이'…서민들 어쩌나</span>            <span class="information">                <span class="source">이데일리</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/018/2025/08/18/0006092340_001_20250818131412296.jpg?type=nf176_176" width="88" height="88" alt="전셋값 폭등에 피할 수 없는 '월세살이'…서민들 어쩌나" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/015/0005171952" target="_blank" class="link">        <span class="text">           <span class="title">21억 찍은 아파트, 한 달 만에 또…대출 규제에도 高高한 동네</span>            <span class="information">                <span class="source">한국경제</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/015/2025/08/18/0005171952_001_20250818140612042.jpg?type=nf176_176" width="88" height="88" alt="21억 찍은 아파트, 한 달 만에 또…대출 규제에도 高高한 동네" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/018/0006092224" target="_blank" class="link">        <span class="text">           <span class="title">"1층도 텅 비었는데 꿈쩍 않는 임대료"…벼랑 끝 신촌 가보니[르포]</span>            <span class="information">                <span class="source">이데일리</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/018/2025/08/18/0006092224_001_20250818055107683.jpg?type=nf176_176" width="88" height="88" alt="&quot;1층도 텅 비었는데 꿈쩍 않는 임대료&quot;…벼랑 끝 신촌 가보니[르포]" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/009/0005542784" target="_blank" class="link">        <span class="text">           <span class="title">용산서 보증금 10억에 월 3천만원 계약됐다…월세 거래 100만건 시대 열려</span>            <span class="information">                <span class="source">매일경제</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/009/2025/08/18/0005542784_001_20250818091908583.png?type=nf176_176" width="88" height="88" alt="용산서 보증금 10억에 월 3천만원 계약됐다…월세 거래 100만건 시대 열려" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/009/0005543173" target="_blank" class="link">        <span class="text">           <span class="title">“이사 걱정에 잠이 안 와요”…정부 제재 예고에 떠는 ‘이 아파트’ 계약자들</span>            <span class="information">                <span class="source">매일경제</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/009/2025/08/18/0005543173_001_20250818170612525.png?type=nf176_176" width="88" height="88" alt="“이사 걱정에 잠이 안 와요”…정부 제재 예고에 떠는 ‘이 아파트’ 계약자들" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/016/0002515535" target="_blank" class="link">        <span class="text">           <span class="title">“공공임대라 안심했는데” 청년안심주택 또 날벼락</span>            <span class="information">                <span class="source">헤럴드경제</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/016/2025/08/18/0002515535_001_20250818112211060.jpg?type=nf176_176" width="88" height="88" alt="“공공임대라 안심했는데” 청년안심주택 또 날벼락" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/011/0004522232" target="_blank" class="link">        <span class="text">           <span class="title">성수 지구별 사업비만 2조대…수주전 '과열'</span>            <span class="information">                <span class="source">서울경제</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/011/2025/08/18/0004522232_001_20250818230232087.jpg?type=nf176_176" width="88" height="88" alt="성수 지구별 사업비만 2조대…수주전 '과열'" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/629/0000417390" target="_blank" class="link">        <span class="text">           <span class="title">"압구정인데 수의계약이라니"…2구역 시공사 선정 놓고 잡음</span>            <span class="information">                <span class="source">더팩트</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/629/2025/08/18/202537791755479391_20250818105316334.jpg?type=nf176_176" width="88" height="88" alt="&quot;압구정인데 수의계약이라니&quot;…2구역 시공사 선정 놓고 잡음" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/014/0005393161" target="_blank" class="link">        <span class="text">           <span class="title">장위동 공공주택서 청년들 수억 보증금 못 받을판</span>            <span class="information">                <span class="source">파이낸셜뉴스</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/014/2025/08/18/0005393161_001_20250818184817203.jpg?type=nf176_176" width="88" height="88" alt="장위동 공공주택서 청년들 수억 보증금 못 받을판" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/366/0001100955" target="_blank" class="link">        <span class="text">           <span class="title">대구 ‘악성 미분양’ 1년 새 2배 급증… 부산도 89.9% 늘어</span>            <span class="information">                <span class="source">조선비즈</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/366/2025/08/18/0001100955_001_20250818105710031.JPG?type=nf176_176" width="88" height="88" alt="대구 ‘악성 미분양’ 1년 새 2배 급증… 부산도 89.9% 늘어" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/016/0002515550" target="_blank" class="link">        <span class="text">           <span class="title">“세입자에 보증금 선지급해달라” 서울시, 1금융권에 SOS</span>            <span class="information">                <span class="source">헤럴드경제</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/016/2025/08/18/0002515550_001_20250818112925711.jpg?type=nf176_176" width="88" height="88" alt="“세입자에 보증금 선지급해달라” 서울시, 1금융권에 SOS" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/032/0003390091" target="_blank" class="link">        <span class="text">           <span class="title">[단독]짓는데 1조, 새 단장에 3조?···배보다 배꼽이 큰 인천공항 리모델링</span>            <span class="information">                <span class="source">경향신문</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/032/2025/08/18/0003390091_001_20250818070214595.jpg?type=nf176_176" width="88" height="88" alt="[단독]짓는데 1조, 새 단장에 3조?···배보다 배꼽이 큰 인천공항 리모델링" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/008/0005237107" target="_blank" class="link">        <span class="text">           <span class="title">"용산·강남 전세 살려면 보증금이"…서울 아파트 계약 절반이 '월세'</span>            <span class="information">                <span class="source">머니투데이</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/008/2025/08/18/0005237107_001_20250818110713324.jpg?type=nf176_176" width="88" height="88" alt="&quot;용산·강남 전세 살려면 보증금이&quot;…서울 아파트 계약 절반이 '월세'" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/009/0005543291" target="_blank" class="link">        <span class="text">           <span class="title">[단독] 공사비 치솟는데 임대료 인하 압박, 사업주는 연10억 적자…청년안심주택도 올스톱</span>            <span class="information">                <span class="source">매일경제</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/009/2025/08/18/0005543291_001_20250818175917808.jpg?type=nf176_176" width="88" height="88" alt="[단독] 공사비 치솟는데 임대료 인하 압박, 사업주는 연10억 적자…청년안심주택도 올스톱" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/417/0001096001" target="_blank" class="link">        <span class="text">           <span class="title">'정권 낙하산 논란' 도로공사 함진규, 국토부 기관장 줄사퇴 속 꼿꼿</span>            <span class="information">                <span class="source">머니S</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/417/2025/08/18/0001096001_001_20250818200109334.jpg?type=nf176_176" width="88" height="88" alt="'정권 낙하산 논란' 도로공사 함진규, 국토부 기관장 줄사퇴 속 꼿꼿" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/016/0002515278" target="_blank" class="link">        <span class="text">           <span class="title">[영상] “주소는 과천 학군은 서초” 과천 첫 디에이치, 견본주택 인산인해 [부동산360]</span>            <span class="information">                <span class="source">헤럴드경제</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/016/2025/08/18/0002515278_001_20250818071808246.jpeg?type=nf176_176" width="88" height="88" alt="[영상] “주소는 과천 학군은 서초” 과천 첫 디에이치, 견본주택 인산인해 [부동산360]" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/119/0002991759" target="_blank" class="link">        <span class="text">           <span class="title">가덕도신공항, 현건 이어 포스코이앤씨 이탈로 다시 ‘적신호’</span>            <span class="information">                <span class="source">데일리안</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/119/2025/08/18/0002991759_001_20250818060117061.jpg?type=nf176_176" width="88" height="88" alt="가덕도신공항, 현건 이어 포스코이앤씨 이탈로 다시 ‘적신호’" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/016/0002515558" target="_blank" class="link">        <span class="text">           <span class="title">사업자 외면에 ‘공급 절벽’ 우려</span>            <span class="information">                <span class="source">헤럴드경제</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/016/2025/08/18/0002515558_001_20250818113011037.jpg?type=nf176_176" width="88" height="88" alt="사업자 외면에 ‘공급 절벽’ 우려" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/020/0003654674" target="_blank" class="link">        <span class="text">           <span class="title">갈지자 집값 통계… 거래량 줄며 몇몇이 흔드는 ‘착시’ 가능성</span>            <span class="information">                <span class="source">동아일보</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/020/2025/08/18/0003654674_001_20250818031014741.jpg?type=nf176_176" width="88" height="88" alt="갈지자 집값 통계… 거래량 줄며 몇몇이 흔드는 ‘착시’ 가능성" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/008/0005236927" target="_blank" class="link">        <span class="text">           <span class="title">부산, 대구서 "신고가!" 속출…'미분양 무덤' 탈출?</span>            <span class="information">                <span class="source">머니투데이</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/008/2025/08/18/0005236927_001_20250818060109827.jpg?type=nf176_176" width="88" height="88" alt="부산, 대구서 &quot;신고가!&quot; 속출…'미분양 무덤' 탈출?" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/421/0008432197" target="_blank" class="link">        <span class="text">           <span class="title">'2조원' 성수1지구 재개발…한강변 초고층 시공권 놓고 '3파전'</span>            <span class="information">                <span class="source">뉴스1</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/421/2025/08/18/0008432197_001_20250818060512112.jpg?type=nf176_176" width="88" height="88" alt="'2조원' 성수1지구 재개발…한강변 초고층 시공권 놓고 '3파전'" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/008/0005237185" target="_blank" class="link">        <span class="text">           <span class="title">강남 '청담르엘'·송파 '잠래아'…SH, 장기전세주택 293가구 공급</span>            <span class="information">                <span class="source">머니투데이</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/008/2025/08/18/0005237185_001_20250818115913527.jpg?type=nf176_176" width="88" height="88" alt="강남 '청담르엘'·송파 '잠래아'…SH, 장기전세주택 293가구 공급" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/009/0005543450" target="_blank" class="link">        <span class="text">           <span class="title">같은 남양주 왕숙인데…왜 ‘여기’만 경쟁률 2~3배 치솟은거야</span>            <span class="information">                <span class="source">매일경제</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/009/2025/08/18/0005543450_001_20250818232613711.png?type=nf176_176" width="88" height="88" alt="같은 남양주 왕숙인데…왜 ‘여기’만 경쟁률 2~3배 치솟은거야" loading="lazy" decoding="async"></span>    </a></li><li class="item" style="">    <a href="https://n.news.naver.com/article/421/0008432158" target="_blank" class="link">        <span class="text">           <span class="title">포스코 빠진 '송파한양2차' 재건축…GS건설·HDC현산 양강 구도</span>            <span class="information">                <span class="source">뉴스1</span>            </span>        </span>        <span class="thumb"><img src="https://imgnews.pstatic.net/image/421/2025/08/18/0008432158_001_20250818093516427.jpg?type=nf176_176" width="88" height="88" alt="포스코 빠진 '송파한양2차' 재건축…GS건설·HDC현산 양강 구도" loading="lazy" decoding="async"></span>    </a></li></ul><div class="button_area"><button type="button" class="buttton_count fold">접기 <span class="icon_arrow">    <svg width="12" height="7" viewBox="0 0 12 7" fill="none" xmlns="http://www.w3.org/2000/svg">        <path d="M1 1L6 6L11 1" stroke="#404048" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"></path>    </svg></span></button></div></div>
    a 태그에 있는 링크들을 모두 접속하여 기사를 모두 수잡합니다.

    **다음 지침을 반드시 따라주세요:**
    1.  **마크다운 형식**으로 작성해주세요.
    2.  글의 가장 첫 줄에는 흥미를 유발할 수 있는 **제목**을 `# 제목` 형식으로 넣어주세요.
    3.  서론, 본론, 결론의 구조를 갖추고, 각 뉴스 내용을 자연스럽게 연결하여 설명해주세요.
    4.  독자들이 이해하기 쉽게 친절하고 전문적인 어조를 사용해주세요.
    5.  이모티콘등을 섞어서 사용해주세요. 단, 첫줄에는 이모티콘을 사용하지 마세요.
    6.  글의 마지막에는 #부동산 #부동산뉴스 #시장분석 #내집마련 등 관련 **태그**를 5개 이상 추가해주세요.
    """

    try:
        response = model.generate_content(prompt)
        print("Gemini 블로그 글 생성 완료!")
        print("\n--- 생성된 블로그 글 내용 ---\n")
        print(response.text)
        print("\n------------------------------\n")
        return response.text
    except Exception as e:
        print(f"Gemini API 요청 중 오류 발생: {e}")
        return None


# --- 3. Tistory 블로그 포스팅 함수 (Selenium) ---
def post_to_tistory_selenium(blog_name, tistory_id, tistory_pw, content):
    """Selenium을 사용하여 Tistory 블로그에 글을 포스팅합니다."""
    print("Selenium을 통해 Tistory 블로그 포스팅을 시작합니다...")

    try:
        # Gemini가 생성한 글의 첫 줄을 제목으로, 나머지를 내용으로 분리
        title = content.split('\n')[0].replace('# ', '').strip()
        post_content = '\n'.join(content.split('\n')[1:]).strip()

        # ChromeDriver BMP-only 에러 방지를 위해 제목에서 특수문자(이모티콘 등) 필터링
        def remove_non_bmp_chars(s):
            return "".join(c for c in s if c <= '\uFFFF')
        title = remove_non_bmp_chars(title)

        # --- 디버깅용 프린트 ---
        print("\n--- DEBUG: TITLE ---")
        print(title)
        print("--- DEBUG: CONTENT ---")
        print(post_content)
        print("----------------------\n")

    except IndexError:
        print("콘텐츠에서 제목을 분리할 수 없습니다. 기본 제목을 사용합니다.")
        title = f"{datetime.now().strftime('%Y년 %m월 %d일')} 부동산 뉴스 브리핑"
        post_content = content

    from selenium.webdriver.chrome.service import Service
    # ... (기존 코드 유지)

    # Selenium WebDriver 설정
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # GitHub Actions 환경에서는 GUI가 없으므로 headless 모드 사용
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # ChromeDriver 서비스 설정
    service = Service(executable_path='./chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 20)

    try:
        # 1. 카카오 로그인 페이지로 직접 이동
        print("카카오 로그인 페이지로 직접 이동합니다.")
        driver.get(
            "https://accounts.kakao.com/login/?continue=https%3A%2F%2Fkauth.kakao.com%2Foauth%2Fauthorize%3Fclient_id%3D3e6ddd834b023f24221217e370daed18%26state%3DaHR0cHM6Ly9ra2Vuc3UudGlzdG9yeS5jb20vbWFuYWdlL25ld3Bvc3Qv%26prompt%3Dselect_account%26redirect_uri%3Dhttps%253A%252F%252Fwww.tistory.com%252Fauth%252Fkakao%252Fredirect%26response_type%3Dcode%26auth_tran_id%3Ddvy6kpj4uxg3e6ddd834b023f24221217e370daed18meh80vuu%26ka%3Dsdk%252F1.43.6%2520os%252Fjavascript%2520sdk_type%252Fjavascript%2520lang%252Fko-KR%2520device%252FMacIntel%2520origin%252Fhttps%25253A%25252F%25252Fwww.tistory.com%26is_popup%3Dfalse%26through_account%3Dtrue#login")

        # 2. 카카오 로그인 페이지에서 아이디/비밀번호 입력 및 로그인
        print("카카오 로그인 페이지로 이동하여 로그인 정보를 입력합니다.")
        # 카카오 로그인 페이지의 URL이 'accounts.kakao.com'을 포함하는지 확인
        wait.until(EC.url_contains("accounts.kakao.com"))

        # 카카오 아이디(이메일 또는 전화번호) 입력 필드
        id_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#loginId--1")))
        id_field.send_keys(tistory_id)

        # 카카오 비밀번호 입력 필드
        pw_field = driver.find_element(By.CSS_SELECTOR, "#password--2")
        pw_field.send_keys(tistory_pw)

        # 로그인 버튼 클릭
        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn_g.highlight.submit")))
        login_button.click()
        print("카카오 로그인 정보 입력 완료.")

        # 3. Tistory 관리 페이지로 리디렉션 대기 및 글쓰기 페이지로 이동
        # 카카오 로그인 후 Tistory 관리 페이지로 돌아올 때까지 기다립니다.
        # TODO: 카카오 로그인 과정 중 추가 인증(예: 2단계 인증, 서비스 연결 동의) 화면이 나타날 경우,
        # 해당 화면을 처리하는 로직을 추가해야 합니다. 현재는 바로 리디렉션된다고 가정합니다.
        print("Tistory 관리 페이지로 리디렉션 대기 중...")
        # Tistory 도메인으로 돌아올 때까지 기다립니다.
        wait.until(EC.url_contains("https://kkensu.tistory.com/manage/newpost"))
        time.sleep(1)

        # "저장된 글이 있습니다" 알림 처리 (취소)
        try:
            print("저장된 글 알림을 확인합니다...")
            # 알림창이 나타날 때까지 최대 3초 대기
            alert_wait = WebDriverWait(driver, 3)
            alert = alert_wait.until(EC.alert_is_present())
            print(f"알림창 발견: {alert.text}")
            alert.dismiss()  # '취소' 버튼 클릭
            print("알림창의 '취소'를 클릭했습니다.")
        except Exception:
            print("저장된 글 알림이 나타나지 않았습니다. 계속 진행합니다.")

        # 4. 카테고리 선택: "부동산"
        print("카테고리를 '부동산'으로 선택합니다.")
        category_dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.mce-btn-type1.select_btn")))
        category_dropdown.click()
        time.sleep(1)

        real_estate_category = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[contains(@class, 'category-item')]/a[text()='부동산']")))
        real_estate_category.click()
        time.sleep(1)

        # 5. 제목 입력
        print("제목을 입력합니다.")
        title_input = wait.until(EC.presence_of_element_located((By.ID, "post-title-inp")))
        title_input.send_keys(title)
        time.sleep(1)

        # 6. 내용 입력 (TinyMCE 에디터 - iframe 처리)
        print("내용을 입력합니다.")
        # TinyMCE 에디터 iframe으로 전환
        wait.until(EC.frame_to_be_available_and_switch_to_it("editor-tistory_ifr"))
        
        # post_content를 HTML 형식으로 변환
        html_content = ""
        for line in post_content.split('\n'):
            if line.strip() == "":
                html_content += '<p data-ke-size="size16"><br data-mce-bogus="1"></p>'
            else:
                html_content += f'<p data-ke-size="size16">{line}</p>'

        # iframe 내부의 TinyMCE body에 내용 주입
        content_body = wait.until(EC.element_to_be_clickable((By.ID, "tinymce")))
        driver.execute_script("arguments[0].innerHTML = arguments[1];", content_body, html_content)

        # 메인 프레임으로 다시 전환
        driver.switch_to.default_content()
        time.sleep(1)

        # 7. 발행 버튼 클릭 (1단계: 완료)
        print("'완료' 버튼을 클릭합니다.")
        publish_layer_btn = wait.until(EC.element_to_be_clickable((By.ID, "publish-layer-btn")))
        publish_layer_btn.click()
        time.sleep(1)

        # 8. 발행 설정 라디오 버튼 클릭
        print("발행 설정 라디오 버튼(id=open20)을 클릭합니다.")
        open20_radio_button = wait.until(EC.element_to_be_clickable((By.ID, "open20")))
        open20_radio_button.click()
        time.sleep(1)

        # 9. 최종 발행 버튼 클릭 (2단계: 공개 발행)
        print("'공개 발행' 버튼을 클릭합니다.")
        final_publish_btn = wait.until(EC.element_to_be_clickable((By.ID, "publish-btn")))
        final_publish_btn.click()

        print("블로그 포스팅 성공!")
        time.sleep(1)  # 포스팅 완료 후 잠시 대기
        print(f"최종 포스팅된 페이지 URL: {driver.current_url}")

    except Exception as e:
        print(f"Selenium 작업 중 오류 발생: {e}")
        # 오류 발생 시 스크린샷 저장 (디버깅용)
        driver.save_screenshot("error_screenshot.png")
    finally:
        driver.quit()


# --- 메인 실행 로직 ---
if __name__ == "__main__":
    # GitHub Actions의 Secrets에서 정보 가져오기
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    tistory_id = os.environ.get("TISTORY_ID")
    tistory_pw = os.environ.get("TISTORY_PW")
    tistory_blog_name = os.environ.get("TISTORY_BLOG_NAME")

    if not all([gemini_api_key, tistory_id, tistory_pw, tistory_blog_name]):
        print("오류: 필요한 환경변수가 설정되지 않았습니다.")
        print("GEMINI_API_KEY, TISTORY_ID, TISTORY_PW, TISTORY_BLOG_NAME를 확인해주세요.")
    else:
        # 1. 블로그 글 생성 (Gemini가 뉴스 검색 포함)
        blog_post_content = generate_post_with_gemini(gemini_api_key)
        # blog_post_content = (f"#블로그 제목\n\n"
        #                      f"이거 내용입니다.")

        if blog_post_content:
            # 2. 블로그 포스팅 (Selenium)
            post_to_tistory_selenium(tistory_blog_name, tistory_id, tistory_pw, blog_post_content)
