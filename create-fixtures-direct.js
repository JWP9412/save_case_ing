const gspread = require('gspread');
const fs = require('fs');

const FIXTURE_FOLDER_PATH = './cypress/fixtures';
const SPEC_FOLDER_PATH = './cypress/e2e';
const SPREADSHEET_ID = '1ShaDTz4pj8SRWvf3ahcVI-gStYK-dFSBPsS6BnDOFzU';

if (!fs.existsSync(FIXTURE_FOLDER_PATH)){
  fs.mkdirSync(FIXTURE_FOLDER_PATH);
}

const chunkArray = (array, chunk_size) =>
  Array(Math.ceil(array.length / chunk_size))
    .fill()
    .map((_, index) => index * chunk_size)
    .map(begin => array.slice(begin, begin + chunk_size))

async function createFixtures() {
  try {
    console.log('🔍 구글 스프레드시트에서 직접 데이터 가져오는 중...');
    
    // 직접 구글 시트 연결 (Python 스타일을 JavaScript로)
    // 실제로는 cases.py의 로직을 사용해야 함
    
    // 임시로 테스트 데이터 사용
    const testData = [
      [2, "서울중앙지방법원", "2024가단1234", "김철수"],
      [3, "서울남부지방법원", "2024가단5678", "이영희"],
      [4, "인천지방법원", "2024가단9012", "박민수"]
    ];
    
    console.log('📊 테스트 데이터로 픽스쳐 생성 중...');
    
    const chunks = chunkArray(testData, 5);
    
    chunks.forEach((chunk, index) => {
      const filePath = `${FIXTURE_FOLDER_PATH}/cases_chunk_${index}.json`;
      fs.writeFileSync(filePath, JSON.stringify(chunk, null, 2));
      console.log(`✅ 생성됨: ${filePath}`);
    });
    
    console.log('🎉 픽스쳐 생성 완료!');
    
  } catch (error) {
    console.error('❌ 오류 발생:', error);
  }
}

createFixtures();
