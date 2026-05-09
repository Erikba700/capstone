// Test Timezone Utilities

import { formatDateTimeWithTimezone, getBrowserTimezone } from './src/utils/timezone';

console.log('Testing Timezone Utilities...\n');

// Test 1: UTC timezone
console.log('Test 1: UTC timezone');
const utcResult = formatDateTimeWithTimezone('2026-05-09', '12:55', 'UTC');
console.log('Result:', utcResult);
console.log('Expected: 2026-05-09T12:55:00+00:00 or 2026-05-09T12:55:00Z');
console.log('Match:', utcResult === '2026-05-09T12:55:00+00:00' || utcResult === '2026-05-09T12:55:00Z' ? '✅' : '❌');
console.log('');

// Test 2: Armenia timezone (GMT+4)
console.log('Test 2: Asia/Yerevan (Armenia, GMT+4)');
const armeniaResult = formatDateTimeWithTimezone('2026-05-09', '12:55', 'Asia/Yerevan');
console.log('Result:', armeniaResult);
console.log('Expected: 2026-05-09T12:55:00+04:00');
console.log('Match:', armeniaResult === '2026-05-09T12:55:00+04:00' ? '✅' : '❌');
console.log('');

// Test 3: New York timezone (GMT-4 or GMT-5 depending on DST)
console.log('Test 3: America/New_York');
const nyResult = formatDateTimeWithTimezone('2026-05-09', '12:55', 'America/New_York');
console.log('Result:', nyResult);
console.log('Expected: Should have -04:00 or -05:00 offset');
console.log('Valid:', nyResult.includes('-04:00') || nyResult.includes('-05:00') ? '✅' : '❌');
console.log('');

// Test 4: Browser timezone
console.log('Test 4: Browser timezone detection');
const browserTz = getBrowserTimezone();
console.log('Detected timezone:', browserTz);
console.log('Valid:', browserTz && browserTz.length > 0 ? '✅' : '❌');
console.log('');

// Test 5: Invalid inputs (should fallback to Z)
console.log('Test 5: Error handling');
try {
  const fallbackResult = formatDateTimeWithTimezone('2026-05-09', '12:55', 'Invalid/Timezone');
  console.log('Result with invalid timezone:', fallbackResult);
  console.log('Should fallback to Z:', fallbackResult.endsWith('Z') || fallbackResult.includes('+00:00') ? '✅' : '❌');
} catch (error) {
  console.log('Error:', error);
}
console.log('');

console.log('All tests completed!');

