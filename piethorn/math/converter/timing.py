from datetime import datetime, timezone


def format_time(years: int, months: int, days: int,
                hours: int, minutes: int, seconds: int,
                milliseconds: int | float=0, microseconds: int | float=0, nanoseconds: int | float=0.0, time_zone="UTC"):
    """
    This function doesn't do any mathematics calculations to format
    the time, this function will only insert the values provided into
    appropriate locations.
    The formatting the values will take is described as follows:

    If nanoseconds isn't zero:
    `year-month-day  hour:minute:second . millisecond;microsecond;nanosecond  time_zone`

    If microseconds isn't zero, but nanoseconds are:
    `year-month-day  hour:minute:second . millisecond;microsecond  time_zone`

    If milliseconds isn't zero, but nanoseconds and microseconds are:
    `year-month-day  hour:minute:second ; millisecond  time_zone`

    If nanoseconds, microseconds, and milliseconds are zero:
    `year-month-day  hour:minute:second  time_zone`

    :param years: The number of years in the time.
    :param months: The number of months in the time.
    :param days: The number of days in the time.
    :param hours: The number of hours in the time.
    :param minutes: The number of minutes in the time.
    :param seconds: The number of seconds in the time.
    :param milliseconds: The number of milliseconds in the time. If this value is zero, then it will be omitted. (Default: 0)
    :param microseconds: The number of microseconds in the time. If this value is zero, then it will be omitted. (Default: 0)
    :param nanoseconds: The number of nanoseconds in the time. If this value is zero, then it will be omitted. (Default: 0)
    :param time_zone: The timezone that the time being formatted is in. If this value is `None` or an empty string, then this value is omitted. (Default: UTC)
    :return: The formatted time.
    """
    formatted_time = f"{years:04d}-{months:02d}-{days:02d}  {hours:02d}:{minutes:02d}:{seconds:02d}"
    if milliseconds != 0 or microseconds != 0 or nanoseconds != 0:
        if microseconds == 0 and nanoseconds == 0:
            formatted_time += f" ; {milliseconds}"
        else:
            formatted_time += f" . {milliseconds}"
    if microseconds != 0 or nanoseconds != 0:
        formatted_time += f";{microseconds}"
    if nanoseconds != 0:
        formatted_time += f";{nanoseconds}"
    if time_zone is not None and time_zone != "":
        formatted_time += f"  {time_zone}"
    return formatted_time


# Define time conversions
SECONDS_IN_YEAR = 31_536_000  # 365 days
SECONDS_IN_MONTH = 2_592_000  # 30 days
SECONDS_IN_DAY = 86_400
SECONDS_IN_HOUR = 3_600
SECONDS_IN_MINUTE = 60
MILLISECONDS_IN_SECOND = 1_000
MICROSECONDS_IN_MILLISECOND = 1_000
NANOSECONDS_IN_MICROSECOND = 1_000

def convert_seconds(x, formatted=False, f_nano=True, f_micro=True, f_milli=True):
    """
    This function converts `x` number of seconds into years, months, days, hours, minutes, seconds, milliseconds, microseconds, and nanoseconds.

    The return of this function can be either a string or a dictionary.
    It'll return a string if `formatted` is `True`, the string will be
    created with the `format_time` function.
    On the other hand, this function will return a dictionary with
    each of the previously stated times that `x` is distributed to.

    :param x: The number of seconds to convert.
    :param formatted: Whether to format the converted seconds into a time format.
    :param f_nano: Whether to format nanoseconds in. This value only matters if `formatted` is `True`.
    :param f_micro: Whether to format microseconds in. If this is false, then `f_nano` will be hard set to false. This value only matters if `formatted` is `True`.
    :param f_milli: Whether to format milliseconds in. If this is false, then `f_micro` and `f_nano` will be hard set to false. This value only matters if `formatted` is `True`.
    :return: The converted time. If `formatted` is `True` then the return is a string. Otherwise, the return will be a dictionary with appropriate values.
    """
    # Calculate each unit
    years = x // SECONDS_IN_YEAR
    x = x % SECONDS_IN_YEAR

    months = x // SECONDS_IN_MONTH
    x = x % SECONDS_IN_MONTH

    days = x // SECONDS_IN_DAY
    x = x % SECONDS_IN_DAY

    hours = x // SECONDS_IN_HOUR
    x = x % SECONDS_IN_HOUR

    minutes = x // SECONDS_IN_MINUTE
    x = x % SECONDS_IN_MINUTE

    seconds = int(x)
    remaining_fraction = x - seconds

    milliseconds = int(remaining_fraction * MILLISECONDS_IN_SECOND)
    remaining_fraction -= milliseconds / MILLISECONDS_IN_SECOND

    microseconds = int(remaining_fraction * MILLISECONDS_IN_SECOND * MICROSECONDS_IN_MILLISECOND)
    remaining_fraction -= microseconds / (MILLISECONDS_IN_SECOND * MICROSECONDS_IN_MILLISECOND)

    nanoseconds = remaining_fraction * MILLISECONDS_IN_SECOND * MICROSECONDS_IN_MILLISECOND * NANOSECONDS_IN_MICROSECOND

    years = int(years)
    months = int(months)
    days = int(days)
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    milliseconds = int(milliseconds)
    microseconds = int(microseconds)

    if formatted:
        # Format output, adding nanoseconds if some exist.
        if f_milli:
            if f_micro:
                if f_nano:
                    return format_time(years, months, days, hours, minutes, seconds, milliseconds, microseconds, nanoseconds, "")
                else:
                    return format_time(years, months, days, hours, minutes, seconds, milliseconds, microseconds, time_zone="")
            else:
                return format_time(years, months, days, hours, minutes, seconds, milliseconds, time_zone="")
        return format_time(years, months, days, hours, minutes, seconds, time_zone="")

    return {
        "years": years,
        "months": months,
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
        "milliseconds": milliseconds,
        "microseconds": microseconds,
        "nanoseconds": nanoseconds
    }


def convert_to_utc(time_input, tpe="sec", formatting="%Y-%m-%d %H:%M:%S.%f"):
    """
    Converts various time formats to UTC with the format:
    year-month-day  hour:minute:second . millisecond;microsecond;nanosecond  UTC

    The types of `tpe`: (Regardless of type, auto-detect will work. type is just there to help manage certain things.)

    * unknown - This is when you don't know the type, so auto-detection will do a bit of extra lifting.

    * date - This is when it's a native datetime.

    * str - For when input was a string.

    * nano - For int/float input that is declared in nanoseconds.

    * micro - For int/float input that is declared in microseconds.

    * milli - For int/float input that is declared in milliseconds.

    * sec - For int/float input that is declared in seconds.

    * minu - For int/float input that is declared in minutes.

    * hr - For int/float input that is declared in hours.

    * d - For int/float input that is declared in days.

    * wk - For int/float input that is declared in weeks.

    * mh - For int/float input that is declared in months.

    * yr - For int/float input that is declared in years.

    * de - For int/float input that is declared in decades.

    * cy - For int/float input that is declared in centuries.

    * mm - For int/float input that is declared in millenniums.

    When the system is converting a numeric, it'll have to try and convert
    the time_input into seconds. This is why it is best to define the type
    for numeric inputs.

    :param time_input: The time to convert.
    :param tpe: The type of value time_input is.
    :param formatting: The type of formatting time_input has, only matters if time_input is a string.
    :return: The string that is the UTC time of the provided time in the format stated at the top of this doc.
    """
    # If input is a numeric timestamp
    if isinstance(time_input, (int, float)):
        if tpe=="nano":
            # Convert nanosecond timestamp to seconds
            time_input = time_input / 1e9
        elif tpe == "micro":
            # Convert microsecond timestamp to second
            time_input = time_input / 1e6
        elif tpe == "milli":
            # Convert millisecond timestamp to seconds
            time_input = time_input / 1000
        elif tpe == "sec":
            pass
        elif tpe == "minu":
            time_input = time_input * 60
        elif tpe == "hr":
            time_input = time_input * 3600
        elif tpe == "d":
            time_input = time_input * 86400
        elif tpe == "wk":
            time_input = time_input * 604800
        elif tpe == "mh":
            time_input = time_input * 2629800
        elif tpe == "yr":
            time_input = time_input * 31557600
        elif tpe == "de":
            time_input = time_input * 315576000
        elif tpe == "cy":
            time_input = time_input * 3155760000
        elif tpe == "mm":
            time_input = time_input * 31557600000
        elif tpe == "unknown":
            if time_input <= 3:
                return convert_to_utc(time_input, "mm", formatting)
            elif time_input <= 30:
                return convert_to_utc(time_input, "cy", formatting)
            elif time_input <= 300:
                return convert_to_utc(time_input, "de", formatting)
            elif time_input <= 3000:
                return convert_to_utc(time_input, "y", formatting)
            elif time_input <= 36000:
                return convert_to_utc(time_input, "mh", formatting)
            elif time_input <= 156536:
                return convert_to_utc(time_input, "wk", formatting)
            elif time_input <= 1095750:
                return convert_to_utc(time_input, "d", formatting)
            elif time_input <= 26298000:
                return convert_to_utc(time_input, "hr", formatting)
            elif time_input <= 1577880000:
                return convert_to_utc(time_input, "minu", formatting)
            elif time_input <= 94672800000:
                pass
            elif time_input <= 94672800000000:
                return convert_to_utc(time_input, "milli", formatting)
            elif time_input <= 94672800000000000:
                return convert_to_utc(time_input, "micro", formatting)
            elif time_input <= 94672800000000000000:
                return convert_to_utc(time_input, "nano", formatting)
            else:
                mad = 94672800000000000000000
                mult = 1e9
                while time_input > mad:
                    mad *= 1000
                    mult *= 1000
                time_input = time_input / mult

        dt = datetime.fromtimestamp(time_input, tz=timezone.utc)
    # If input is a datetime object
    elif isinstance(time_input, datetime):
        dt = time_input.astimezone(timezone.utc)
    # If input is a formatted time string
    elif isinstance(time_input, str):
        try:
            dt = datetime.fromisoformat(time_input)
        except ValueError:
            try:
                dt = datetime.strptime(time_input, formatting)
            except ValueError:
                raise ValueError("Incorrect time string format")
        dt = dt.astimezone(timezone.utc)
    else:
        raise TypeError("Unsupported time format")

    if not isinstance(dt, datetime):
        raise RuntimeError("The given input of time has failed to be properly processed.")

    return format_time(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond/1000)

if __name__ == "__main__":
    print(convert_to_utc(1700000000))
    print(datetime.fromtimestamp(1700000000, tz=timezone.utc))
    print(convert_to_utc("2023-01-01 12:30:45.123456"))
    print(convert_to_utc(1700000000123456789, "nano"))
    print(convert_to_utc("2023-01-01 12:30:45.123456789"))
    print(convert_to_utc(datetime.now()))
