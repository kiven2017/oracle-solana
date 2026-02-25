// 测试 Node fetch 功能
const testFetch = async () => {
  try {
    console.log('Testing fetch to Devnet...');
    const response = await fetch('https://api.devnet.solana.com', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'getHealth'
      })
    });
    const data = await response.json();
    console.log('Success:', data);
  } catch (error) {
    console.error('Error:', error.message);
    console.error('Type:', error.constructor.name);
  }
};

testFetch();
