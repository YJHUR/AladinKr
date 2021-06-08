
# AladinKr
[Calibre](https://calibre-ebook.com)의 metadata plugin입니다.

기존에 있었던 [aladin.co.kr](https://github.com/sseeookk/Calibre-Aladin.co.kr-Metadata-Source-Plugin)이라는 플러그인이 제 맥북에서 돌지 않아 최대한 간단하게 제가 필요했던 기능만 구현했습니다. Calibre 5.x 버전의 기본 구글 서치 코드를 베이스로 수정하여 만들었습니다.

## Install
1. 공개된 소스코드가 아닌 zip file을 다운받습니다.
2. Calibre의 환경설정에서 플러그인 항목으로 가신 뒤 파일에서 플러그인 불러오기
3. 다운로드 받은 zip file을 찾아서 열어준 뒤 진행 네 네 네

## Tips
1. AladinKr로 검사된 정보를 저장하시면 aladin이라는 새로운 구분자가 생성됩니다. 알라딘 사이트의 상품번호입니다.
2. 해외도서나 음반, DVD등의 검색도 필요한 경우가 있어 모두 검색되도록 했습니다. 결과를 선택할 때 주의 바랍니다.
3. 검색어에 '태백산맥 1권' 등으로 입력하면 알라딘 검색이 잘 되지 않습니다. 알라딘 사이트의 검색 페이지 작동 방식이 그런것 같습니다. '태백산맥 1' 로 검색해주세요.
4. 같은 원리로 '김난주 역' 등의 검색도 잘 안됩니다. '김난주' 로 검색해주세요. '권', '역', '지음' 등의 수식어는 지우고 검색하시는게 좋습니다.
5. 만약 isbn이 입력되어있다면 isbn 검색만 진행합니다. aladin id가 입력되어 있다면 검색없이 해당 알라딘 상품을 가져옵니다.
6. [sseeookk](https://github.com/sseeookk/Calibre-Aladin.co.kr-Metadata-Source-Plugin/commits?author=sseeookk)님의 [aladin.co.kr](https://github.com/sseeookk/Calibre-Aladin.co.kr-Metadata-Source-Plugin) plug-in에서 사용하던 aladin.co.kr id는 aladin id로 자동으로 인식합니다. **검색결과를 저장하면 aladin.co.kr를 aladin으로 자동 변환하여 저장합니다!**
7. 종종 19세 연령제한 도서가 존재합니다. 로그인을 하지 않으면 도서 정보를 불러오지 못합니다만, 보안등의 여러가지 이유로 로그인 기능을 구현하지 않았습니다. 그럼에도 플러그인을 통해 정보를 불러오고 싶다면 아래의 방법을 통해 사용이 가능합니다.


## 연령제한 도서 이용 방법
로그인이 되지 않은 상태에서 [소돔의 120일](https://www.aladin.co.kr/shop/wproduct.aspx?ItemId=18862134)이란 책의 상품 페이지를 들어가면 경고가 뜨면서 로그인을 요구합니다. 로그인 한 뒤 들어가주면 해당 제품의 페이지 주소가 다음과 같습니다.
https://www.aladin.co.kr/shop/wproduct.aspx?ItemId=18862134
aladdin id인 18862134을 잘 복사해두시고 브라우저에서 우클릭을 하여 페이지 소스 보기를 들어갑니다. 인터넷 페이지 코드가 뜨면 다시 별도저장 등을 통해 18862134.html 이라는 파일로 바탕화면에 저장합니다. 이후 플러그인을 실행하면 저장된 파일을 통해 정보를 읽어옵니다. 작업이 끝나면 바탕화면의 파일은 지웁니다.

## 당부의 말
전문 개발자가 아니고 취미로 만들어봤습니다. 피드백을 주시면 최대한 반영해보겠으나 빠릿빠릿하게 작업이 되지 않을 수 있습니다.
