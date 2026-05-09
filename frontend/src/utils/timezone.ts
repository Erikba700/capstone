/**
 * Timezone utilities for handling datetime conversions
 */

// Common timezones that users might select
export const COMMON_TIMEZONES = [
  { value: 'UTC', label: 'UTC (Coordinated Universal Time)', offset: '+00:00' },
  { value: 'America/New_York', label: 'America/New York (Eastern Time)', offset: '-05:00/-04:00' },
  { value: 'America/Chicago', label: 'America/Chicago (Central Time)', offset: '-06:00/-05:00' },
  { value: 'America/Denver', label: 'America/Denver (Mountain Time)', offset: '-07:00/-06:00' },
  { value: 'America/Los_Angeles', label: 'America/Los Angeles (Pacific Time)', offset: '-08:00/-07:00' },
  { value: 'Europe/London', label: 'Europe/London (British Time)', offset: '+00:00/+01:00' },
  { value: 'Europe/Paris', label: 'Europe/Paris (Central European Time)', offset: '+01:00/+02:00' },
  { value: 'Europe/Moscow', label: 'Europe/Moscow (Moscow Time)', offset: '+03:00' },
  { value: 'Asia/Dubai', label: 'Asia/Dubai (Gulf Time)', offset: '+04:00' },
  { value: 'Asia/Yerevan', label: 'Asia/Yerevan (Armenia Time)', offset: '+04:00' },
  { value: 'Asia/Kolkata', label: 'Asia/Kolkata (India Time)', offset: '+05:30' },
  { value: 'Asia/Shanghai', label: 'Asia/Shanghai (China Time)', offset: '+08:00' },
  { value: 'Asia/Tokyo', label: 'Asia/Tokyo (Japan Time)', offset: '+09:00' },
  { value: 'Australia/Sydney', label: 'Australia/Sydney (Australian Eastern Time)', offset: '+10:00/+11:00' },
];

/**
 * Get the browser's detected timezone
 */
export function getBrowserTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch (error) {
    console.warn('Could not detect browser timezone, defaulting to UTC');
    return 'UTC';
  }
}

/**
 * Format a date and time to ISO 8601 format with timezone offset
 * @param date - Date string (YYYY-MM-DD)
 * @param time - Time string (HH:mm)
 * @param timezone - IANA timezone string (e.g., 'Asia/Yerevan')
 * @returns ISO 8601 formatted datetime string with timezone offset
 */
export function formatDateTimeWithTimezone(
  date: string,
  time: string,
  timezone: string = 'UTC'
): string {
  if (!date || !time) {
    throw new Error('Both date and time are required');
  }

  try {
    // Combine date and time
    const dateTimeString = `${date}T${time}:00`;

    // Create a date object (will be interpreted as local time)
    const dateObj = new Date(dateTimeString);

    // Validate the date is valid
    if (isNaN(dateObj.getTime())) {
      throw new Error('Invalid date or time format');
    }

    // Get the timezone offset for the given timezone at this specific date/time
    const offset = getTimezoneOffset(dateObj, timezone);

    // Validate offset format
    if (!offset.match(/^[+-]\d{2}:\d{2}$/)) {
      console.error('Invalid offset format:', offset);
      // Fallback to UTC
      return `${dateTimeString}Z`;
    }

    // Format the datetime with the timezone offset
    return `${dateTimeString}${offset}`;
  } catch (error) {
    console.error('Error formatting datetime with timezone:', error);
    // Fallback to UTC
    return `${date}T${time}:00Z`;
  }
}

/**
 * Get the timezone offset for a specific date and timezone
 * @param date - JavaScript Date object
 * @param timezone - IANA timezone string
 * @returns Offset string in format +HH:mm or -HH:mm
 */
function getTimezoneOffset(date: Date, timezone: string): string {
  try {
    // Get UTC time in milliseconds
    const utcTime = date.getTime();

    // Format the date in the target timezone
    const formatter = new Intl.DateTimeFormat('en-US', {
      timeZone: timezone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });

    // Get the formatted parts
    const parts = formatter.formatToParts(date);
    const year = parts.find(p => p.type === 'year')?.value;
    const month = parts.find(p => p.type === 'month')?.value;
    const day = parts.find(p => p.type === 'day')?.value;
    const hour = parts.find(p => p.type === 'hour')?.value;
    const minute = parts.find(p => p.type === 'minute')?.value;
    const second = parts.find(p => p.type === 'second')?.value;

    // Create a proper ISO datetime string
    const tzDateStr = `${year}-${month}-${day}T${hour}:${minute}:${second}`;

    // Parse as UTC to get the time in milliseconds
    const tzTime = Date.parse(tzDateStr + 'Z');

    // Calculate offset in minutes
    // The offset is: (local time as if it were UTC) - (actual UTC time)
    // For GMT+4: when it's 12:59 local, UTC is 08:59
    // So: 12:59 (as UTC ms) - 08:59 (UTC ms) = +4 hours = +240 minutes
    const offsetMinutes = Math.round((tzTime - utcTime) / 60000);

    // Format offset as +/-HH:mm
    const sign = offsetMinutes >= 0 ? '+' : '-';
    const absOffset = Math.abs(offsetMinutes);
    const hours = Math.floor(absOffset / 60).toString().padStart(2, '0');
    const minutes = (absOffset % 60).toString().padStart(2, '0');

    return `${sign}${hours}:${minutes}`;
  } catch (error) {
    console.error('Error calculating timezone offset:', error);
    return '+00:00'; // Default to UTC
  }
}

/**
 * Convert UTC datetime to user's local timezone for display
 * @param utcDatetime - ISO 8601 datetime string in UTC
 * @param timezone - IANA timezone string
 * @returns Formatted datetime string in user's timezone
 */
export function formatUTCToLocalTimezone(
  utcDatetime: string,
  timezone: string = 'UTC'
): string {
  try {
    const date = new Date(utcDatetime);

    const formatter = new Intl.DateTimeFormat('en-US', {
      timeZone: timezone,
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });

    return formatter.format(date);
  } catch (error) {
    console.error('Error formatting UTC to local timezone:', error);
    return utcDatetime;
  }
}

/**
 * Get the minimum datetime value for input field (now in user's timezone)
 * @param timezone - IANA timezone string
 * @returns Object with date and time strings
 */
export function getMinDateTimeInTimezone(timezone: string = 'UTC'): {
  date: string;
  time: string;
} {
  try {
    const now = new Date();

    const formatter = new Intl.DateTimeFormat('en-US', {
      timeZone: timezone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });

    const parts = formatter.formatToParts(now);
    const year = parts.find(p => p.type === 'year')?.value;
    const month = parts.find(p => p.type === 'month')?.value;
    const day = parts.find(p => p.type === 'day')?.value;
    const hour = parts.find(p => p.type === 'hour')?.value;
    const minute = parts.find(p => p.type === 'minute')?.value;

    if (!year || !month || !day || !hour || !minute) {
      throw new Error('Could not parse date parts');
    }

    return {
      date: `${year}-${month}-${day}`,
      time: `${hour}:${minute}`,
    };
  } catch (error) {
    console.error('Error getting min datetime:', error);
    // Fallback to UTC
    const now = new Date();
    return {
      date: now.toISOString().split('T')[0],
      time: now.toISOString().split('T')[1].substring(0, 5),
    };
  }
}

/**
 * Validate if a timezone string is valid
 * @param timezone - IANA timezone string to validate
 * @returns true if valid, false otherwise
 */
export function isValidTimezone(timezone: string): boolean {
  try {
    Intl.DateTimeFormat(undefined, { timeZone: timezone });
    return true;
  } catch (error) {
    return false;
  }
}




