// Script to check localStorage user data
console.log('=== LocalStorage User Data ===');
const userData = localStorage.getItem('user');
if (userData) {
  try {
    const parsed = JSON.parse(userData);
    console.log('User data:', parsed);
    console.log('Username:', parsed.username);
    console.log('Role:', parsed.profile?.role);
  } catch (e) {
    console.log('Error parsing user data:', e);
    console.log('Raw data:', userData);
  }
} else {
  console.log('No user data found in localStorage');
}

console.log('=== Token Data ===');
const token = localStorage.getItem('token');
console.log('Token exists:', !!token);