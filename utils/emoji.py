"""
Regular expressions for matching emoji sequences.

For parsing single emoji, use either

    re.match(EMOJI_SEQUENCE, string)
    # or
    EMOJI_REGEXP.match(string)
    
To match multiple emojis or custom patterns, insert `EMOJI_SEQUENCE` into pattern:

    re.match(rf"{EMOJI_SEQUENCE}+\s*...", string)
"""
# This code was stolen- I mean borrowed from https://gist.github.com/Saluev/604c9c3a3d6032770e15a0da143f73bd
# Props to them for making this working emoji detector

import re

# https://www.unicode.org/Public/emoji/12.1/emoji-data.txt
EMOJI_CHARACTER = (
    "["
    "\u0023"
    "\u002A"
    "\u0030-\u0039"
    "\u00A9"
    "\u00AE"
    "\u203C"
    "\u2049"
    "\u2122"
    "\u2139"
    "\u2194-\u2199"
    "\u21A9-\u21AA"
    "\u231A-\u231B"
    "\u2328"
    "\u23CF"
    "\u23E9-\u23F3"
    "\u23F8-\u23FA"
    "\u24C2"
    "\u25AA-\u25AB"
    "\u25B6"
    "\u25C0"
    "\u25FB-\u25FE"
    "\u2600-\u2604"
    "\u260E"
    "\u2611"
    "\u2614-\u2615"
    "\u2618"
    "\u261D"
    "\u2620"
    "\u2622-\u2623"
    "\u2626"
    "\u262A"
    "\u262E-\u262F"
    "\u2638-\u263A"
    "\u2640"
    "\u2642"
    "\u2648-\u2653"
    "\u265F"
    "\u2660"
    "\u2663"
    "\u2665-\u2666"
    "\u2668"
    "\u267B"
    "\u267E"
    "\u267F"
    "\u2692-\u2694"
    "\u2695"
    "\u2696-\u2697"
    "\u2699"
    "\u269B-\u269C"
    "\u26A0-\u26A1"
    "\u26AA-\u26AB"
    "\u26B0-\u26B1"
    "\u26BD-\u26BE"
    "\u26C4-\u26C5"
    "\u26C8"
    "\u26CE-\u26CF"
    "\u26D1"
    "\u26D3-\u26D4"
    "\u26E9-\u26EA"
    "\u26F0-\u26F5"
    "\u26F7-\u26FA"
    "\u26FD"
    "\u2702"
    "\u2705"
    "\u2708-\u270D"
    "\u270F"
    "\u2712"
    "\u2714"
    "\u2716"
    "\u271D"
    "\u2721"
    "\u2728"
    "\u2733-\u2734"
    "\u2744"
    "\u2747"
    "\u274C"
    "\u274E"
    "\u2753-\u2755"
    "\u2757"
    "\u2763-\u2764"
    "\u2795-\u2797"
    "\u27A1"
    "\u27B0"
    "\u27BF"
    "\u2934-\u2935"
    "\u2B05-\u2B07"
    "\u2B1B-\u2B1C"
    "\u2B50"
    "\u2B55"
    "\u3030"
    "\u303D"
    "\u3297"
    "\u3299"
    "\U0001F004"
    "\U0001F0CF"
    "\U0001F170-\U0001F171"
    "\U0001F17E-\U0001F17F"
    "\U0001F18E"
    "\U0001F191-\U0001F19A"
    "\U0001F1E6-\U0001F1FF"
    "\U0001F201-\U0001F202"
    "\U0001F21A"
    "\U0001F22F"
    "\U0001F232-\U0001F23A"
    "\U0001F250-\U0001F251"
    "\U0001F300-\U0001F321"
    "\U0001F324-\U0001F393"
    "\U0001F396-\U0001F397"
    "\U0001F399-\U0001F39B"
    "\U0001F39E-\U0001F3F0"
    "\U0001F3F3-\U0001F3F5"
    "\U0001F3F7-\U0001F4FD"
    "\U0001F4FF-\U0001F53D"
    "\U0001F549-\U0001F54E"
    "\U0001F550-\U0001F567"
    "\U0001F56F-\U0001F570"
    "\U0001F573-\U0001F579"
    "\U0001F57A"
    "\U0001F587"
    "\U0001F58A-\U0001F58D"
    "\U0001F590"
    "\U0001F595-\U0001F596"
    "\U0001F5A4"
    "\U0001F5A5"
    "\U0001F5A8"
    "\U0001F5B1-\U0001F5B2"
    "\U0001F5BC"
    "\U0001F5C2-\U0001F5C4"
    "\U0001F5D1-\U0001F5D3"
    "\U0001F5DC-\U0001F5DE"
    "\U0001F5E1"
    "\U0001F5E3"
    "\U0001F5E8"
    "\U0001F5EF"
    "\U0001F5F3"
    "\U0001F5FA-\U0001F64F"
    "\U0001F680-\U0001F6C5"
    "\U0001F6CB-\U0001F6D0"
    "\U0001F6D1-\U0001F6D2"
    "\U0001F6D5"
    "\U0001F6E0-\U0001F6E5"
    "\U0001F6E9"
    "\U0001F6EB-\U0001F6EC"
    "\U0001F6F0"
    "\U0001F6F3"
    "\U0001F6F4-\U0001F6F6"
    "\U0001F6F7-\U0001F6F8"
    "\U0001F6F9"
    "\U0001F6FA"
    "\U0001F7E0-\U0001F7EB"
    "\U0001F90D-\U0001F90F"
    "\U0001F910-\U0001F918"
    "\U0001F919-\U0001F91E"
    "\U0001F91F"
    "\U0001F920-\U0001F927"
    "\U0001F928-\U0001F92F"
    "\U0001F930"
    "\U0001F931-\U0001F932"
    "\U0001F933-\U0001F93A"
    "\U0001F93C-\U0001F93E"
    "\U0001F93F"
    "\U0001F940-\U0001F945"
    "\U0001F947-\U0001F94B"
    "\U0001F94C"
    "\U0001F94D-\U0001F94F"
    "\U0001F950-\U0001F95E"
    "\U0001F95F-\U0001F96B"
    "\U0001F96C-\U0001F970"
    "\U0001F971"
    "\U0001F973-\U0001F976"
    "\U0001F97A"
    "\U0001F97B"
    "\U0001F97C-\U0001F97F"
    "\U0001F980-\U0001F984"
    "\U0001F985-\U0001F991"
    "\U0001F992-\U0001F997"
    "\U0001F998-\U0001F9A2"
    "\U0001F9A5-\U0001F9AA"
    "\U0001F9AE-\U0001F9AF"
    "\U0001F9B0-\U0001F9B9"
    "\U0001F9BA-\U0001F9BF"
    "\U0001F9C0"
    "\U0001F9C1-\U0001F9C2"
    "\U0001F9C3-\U0001F9CA"
    "\U0001F9CD-\U0001F9CF"
    "\U0001F9D0-\U0001F9E6"
    "\U0001F9E7-\U0001F9FF"
    "\U0001FA70-\U0001FA73"
    "\U0001FA78-\U0001FA7A"
    "\U0001FA80-\U0001FA82"
    "\U0001FA90-\U0001FA95"
    "]"
)
EXTENDED_PICTOGRAPHIC_CHARACTER = (
    "["
    "\u00A9"
    "\u00AE"
    "\u203C"
    "\u2049"
    "\u2122"
    "\u2139"
    "\u2194-\u2199"
    "\u21A9-\u21AA"
    "\u231A-\u231B"
    "\u2328"
    "\u2388"
    "\u23CF"
    "\u23E9-\u23F3"
    "\u23F8-\u23FA"
    "\u24C2"
    "\u25AA-\u25AB"
    "\u25B6"
    "\u25C0"
    "\u25FB-\u25FE"
    "\u2600-\u2604"
    "\u2605"
    "\u2607-\u260D"
    "\u260E"
    "\u260F-\u2610"
    "\u2611"
    "\u2612"
    "\u2614-\u2615"
    "\u2616-\u2617"
    "\u2618"
    "\u2619-\u261C"
    "\u261D"
    "\u261E-\u261F"
    "\u2620"
    "\u2621"
    "\u2622-\u2623"
    "\u2624-\u2625"
    "\u2626"
    "\u2627-\u2629"
    "\u262A"
    "\u262B-\u262D"
    "\u262E-\u262F"
    "\u2630-\u2637"
    "\u2638-\u263A"
    "\u263B-\u263F"
    "\u2640"
    "\u2641"
    "\u2642"
    "\u2643-\u2647"
    "\u2648-\u2653"
    "\u2654-\u265E"
    "\u265F"
    "\u2660"
    "\u2661-\u2662"
    "\u2663"
    "\u2664"
    "\u2665-\u2666"
    "\u2667"
    "\u2668"
    "\u2669-\u267A"
    "\u267B"
    "\u267C-\u267D"
    "\u267E"
    "\u267F"
    "\u2680-\u2685"
    "\u2690-\u2691"
    "\u2692-\u2694"
    "\u2695"
    "\u2696-\u2697"
    "\u2698"
    "\u2699"
    "\u269A"
    "\u269B-\u269C"
    "\u269D-\u269F"
    "\u26A0-\u26A1"
    "\u26A2-\u26A9"
    "\u26AA-\u26AB"
    "\u26AC-\u26AF"
    "\u26B0-\u26B1"
    "\u26B2-\u26BC"
    "\u26BD-\u26BE"
    "\u26BF-\u26C3"
    "\u26C4-\u26C5"
    "\u26C6-\u26C7"
    "\u26C8"
    "\u26C9-\u26CD"
    "\u26CE-\u26CF"
    "\u26D0"
    "\u26D1"
    "\u26D2"
    "\u26D3-\u26D4"
    "\u26D5-\u26E8"
    "\u26E9-\u26EA"
    "\u26EB-\u26EF"
    "\u26F0-\u26F5"
    "\u26F6"
    "\u26F7-\u26FA"
    "\u26FB-\u26FC"
    "\u26FD"
    "\u26FE-\u2701"
    "\u2702"
    "\u2703-\u2704"
    "\u2705"
    "\u2708-\u270D"
    "\u270E"
    "\u270F"
    "\u2710-\u2711"
    "\u2712"
    "\u2714"
    "\u2716"
    "\u271D"
    "\u2721"
    "\u2728"
    "\u2733-\u2734"
    "\u2744"
    "\u2747"
    "\u274C"
    "\u274E"
    "\u2753-\u2755"
    "\u2757"
    "\u2763-\u2764"
    "\u2765-\u2767"
    "\u2795-\u2797"
    "\u27A1"
    "\u27B0"
    "\u27BF"
    "\u2934-\u2935"
    "\u2B05-\u2B07"
    "\u2B1B-\u2B1C"
    "\u2B50"
    "\u2B55"
    "\u3030"
    "\u303D"
    "\u3297"
    "\u3299"
    "\U0001F000-\U0001F003"
    "\U0001F004"
    "\U0001F005-\U0001F0CE"
    "\U0001F0CF"
    "\U0001F0D0-\U0001F0FF"
    "\U0001F10D-\U0001F10F"
    "\U0001F12F"
    "\U0001F16C-\U0001F16F"
    "\U0001F170-\U0001F171"
    "\U0001F17E-\U0001F17F"
    "\U0001F18E"
    "\U0001F191-\U0001F19A"
    "\U0001F1AD-\U0001F1E5"
    "\U0001F201-\U0001F202"
    "\U0001F203-\U0001F20F"
    "\U0001F21A"
    "\U0001F22F"
    "\U0001F232-\U0001F23A"
    "\U0001F23C-\U0001F23F"
    "\U0001F249-\U0001F24F"
    "\U0001F250-\U0001F251"
    "\U0001F252-\U0001F2FF"
    "\U0001F300-\U0001F321"
    "\U0001F322-\U0001F323"
    "\U0001F324-\U0001F393"
    "\U0001F394-\U0001F395"
    "\U0001F396-\U0001F397"
    "\U0001F398"
    "\U0001F399-\U0001F39B"
    "\U0001F39C-\U0001F39D"
    "\U0001F39E-\U0001F3F0"
    "\U0001F3F1-\U0001F3F2"
    "\U0001F3F3-\U0001F3F5"
    "\U0001F3F6"
    "\U0001F3F7-\U0001F3FA"
    "\U0001F400-\U0001F4FD"
    "\U0001F4FE"
    "\U0001F4FF-\U0001F53D"
    "\U0001F546-\U0001F548"
    "\U0001F549-\U0001F54E"
    "\U0001F54F"
    "\U0001F550-\U0001F567"
    "\U0001F568-\U0001F56E"
    "\U0001F56F-\U0001F570"
    "\U0001F571-\U0001F572"
    "\U0001F573-\U0001F579"
    "\U0001F57A"
    "\U0001F57B-\U0001F586"
    "\U0001F587"
    "\U0001F588-\U0001F589"
    "\U0001F58A-\U0001F58D"
    "\U0001F58E-\U0001F58F"
    "\U0001F590"
    "\U0001F591-\U0001F594"
    "\U0001F595-\U0001F596"
    "\U0001F597-\U0001F5A3"
    "\U0001F5A4"
    "\U0001F5A5"
    "\U0001F5A6-\U0001F5A7"
    "\U0001F5A8"
    "\U0001F5A9-\U0001F5B0"
    "\U0001F5B1-\U0001F5B2"
    "\U0001F5B3-\U0001F5BB"
    "\U0001F5BC"
    "\U0001F5BD-\U0001F5C1"
    "\U0001F5C2-\U0001F5C4"
    "\U0001F5C5-\U0001F5D0"
    "\U0001F5D1-\U0001F5D3"
    "\U0001F5D4-\U0001F5DB"
    "\U0001F5DC-\U0001F5DE"
    "\U0001F5DF-\U0001F5E0"
    "\U0001F5E1"
    "\U0001F5E2"
    "\U0001F5E3"
    "\U0001F5E4-\U0001F5E7"
    "\U0001F5E8"
    "\U0001F5E9-\U0001F5EE"
    "\U0001F5EF"
    "\U0001F5F0-\U0001F5F2"
    "\U0001F5F3"
    "\U0001F5F4-\U0001F5F9"
    "\U0001F5FA-\U0001F64F"
    "\U0001F680-\U0001F6C5"
    "\U0001F6C6-\U0001F6CA"
    "\U0001F6CB-\U0001F6D0"
    "\U0001F6D1-\U0001F6D2"
    "\U0001F6D3-\U0001F6D4"
    "\U0001F6D5"
    "\U0001F6D6-\U0001F6DF"
    "\U0001F6E0-\U0001F6E5"
    "\U0001F6E6-\U0001F6E8"
    "\U0001F6E9"
    "\U0001F6EA"
    "\U0001F6EB-\U0001F6EC"
    "\U0001F6ED-\U0001F6EF"
    "\U0001F6F0"
    "\U0001F6F1-\U0001F6F2"
    "\U0001F6F3"
    "\U0001F6F4-\U0001F6F6"
    "\U0001F6F7-\U0001F6F8"
    "\U0001F6F9"
    "\U0001F6FA"
    "\U0001F6FB-\U0001F6FF"
    "\U0001F774-\U0001F77F"
    "\U0001F7D5-\U0001F7DF"
    "\U0001F7E0-\U0001F7EB"
    "\U0001F7EC-\U0001F7FF"
    "\U0001F80C-\U0001F80F"
    "\U0001F848-\U0001F84F"
    "\U0001F85A-\U0001F85F"
    "\U0001F888-\U0001F88F"
    "\U0001F8AE-\U0001F8FF"
    "\U0001F90C"
    "\U0001F90D-\U0001F90F"
    "\U0001F910-\U0001F918"
    "\U0001F919-\U0001F91E"
    "\U0001F91F"
    "\U0001F920-\U0001F927"
    "\U0001F928-\U0001F92F"
    "\U0001F930"
    "\U0001F931-\U0001F932"
    "\U0001F933-\U0001F93A"
    "\U0001F93C-\U0001F93E"
    "\U0001F93F"
    "\U0001F940-\U0001F945"
    "\U0001F947-\U0001F94B"
    "\U0001F94C"
    "\U0001F94D-\U0001F94F"
    "\U0001F950-\U0001F95E"
    "\U0001F95F-\U0001F96B"
    "\U0001F96C-\U0001F970"
    "\U0001F971"
    "\U0001F972"
    "\U0001F973-\U0001F976"
    "\U0001F977-\U0001F979"
    "\U0001F97A"
    "\U0001F97B"
    "\U0001F97C-\U0001F97F"
    "\U0001F980-\U0001F984"
    "\U0001F985-\U0001F991"
    "\U0001F992-\U0001F997"
    "\U0001F998-\U0001F9A2"
    "\U0001F9A3-\U0001F9A4"
    "\U0001F9A5-\U0001F9AA"
    "\U0001F9AB-\U0001F9AD"
    "\U0001F9AE-\U0001F9AF"
    "\U0001F9B0-\U0001F9B9"
    "\U0001F9BA-\U0001F9BF"
    "\U0001F9C0"
    "\U0001F9C1-\U0001F9C2"
    "\U0001F9C3-\U0001F9CA"
    "\U0001F9CB-\U0001F9CC"
    "\U0001F9CD-\U0001F9CF"
    "\U0001F9D0-\U0001F9E6"
    "\U0001F9E7-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FA73"
    "\U0001FA74-\U0001FA77"
    "\U0001FA78-\U0001FA7A"
    "\U0001FA7B-\U0001FA7F"
    "\U0001FA80-\U0001FA82"
    "\U0001FA83-\U0001FA8F"
    "\U0001FA90-\U0001FA95"
    "\U0001FA96-\U0001FFFD"
    "]"
)
DEFAULT_EMOJI_PRESENTATION_CHARACTER = (
    "["
    "\u231A-\u231B"
    "\u23E9-\u23EC"
    "\u23F0"
    "\u23F3"
    "\u25FD-\u25FE"
    "\u2614-\u2615"
    "\u2648-\u2653"
    "\u267F"
    "\u2693"
    "\u26A1"
    "\u26AA-\u26AB"
    "\u26BD-\u26BE"
    "\u26C4-\u26C5"
    "\u26CE"
    "\u26D4"
    "\u26EA"
    "\u26F2-\u26F3"
    "\u26F5"
    "\u26FA"
    "\u26FD"
    "\u2705"
    "\u270A-\u270B"
    "\u2728"
    "\u274C"
    "\u274E"
    "\u2753-\u2755"
    "\u2757"
    "\u2795-\u2797"
    "\u27B0"
    "\u27BF"
    "\u2B1B-\u2B1C"
    "\u2B50"
    "\u2B55"
    "\U0001F004"
    "\U0001F0CF"
    "\U0001F18E"
    "\U0001F191-\U0001F19A"
    "\U0001F1E6-\U0001F1FF"
    "\U0001F201"
    "\U0001F21A"
    "\U0001F22F"
    "\U0001F232-\U0001F236"
    "\U0001F238-\U0001F23A"
    "\U0001F250-\U0001F251"
    "\U0001F300-\U0001F320"
    "\U0001F32D-\U0001F335"
    "\U0001F337-\U0001F37C"
    "\U0001F37E-\U0001F393"
    "\U0001F3A0-\U0001F3CA"
    "\U0001F3CF-\U0001F3D3"
    "\U0001F3E0-\U0001F3F0"
    "\U0001F3F4"
    "\U0001F3F8-\U0001F43E"
    "\U0001F440"
    "\U0001F442-\U0001F4FC"
    "\U0001F4FF-\U0001F53D"
    "\U0001F54B-\U0001F54E"
    "\U0001F550-\U0001F567"
    "\U0001F57A"
    "\U0001F595-\U0001F596"
    "\U0001F5A4"
    "\U0001F5FB-\U0001F64F"
    "\U0001F680-\U0001F6C5"
    "\U0001F6CC"
    "\U0001F6D0"
    "\U0001F6D1-\U0001F6D2"
    "\U0001F6D5"
    "\U0001F6EB-\U0001F6EC"
    "\U0001F6F4-\U0001F6F6"
    "\U0001F6F7-\U0001F6F8"
    "\U0001F6F9"
    "\U0001F6FA"
    "\U0001F7E0-\U0001F7EB"
    "\U0001F90D-\U0001F90F"
    "\U0001F910-\U0001F918"
    "\U0001F919-\U0001F91E"
    "\U0001F91F"
    "\U0001F920-\U0001F927"
    "\U0001F928-\U0001F92F"
    "\U0001F930"
    "\U0001F931-\U0001F932"
    "\U0001F933-\U0001F93A"
    "\U0001F93C-\U0001F93E"
    "\U0001F93F"
    "\U0001F940-\U0001F945"
    "\U0001F947-\U0001F94B"
    "\U0001F94C"
    "\U0001F94D-\U0001F94F"
    "\U0001F950-\U0001F95E"
    "\U0001F95F-\U0001F96B"
    "\U0001F96C-\U0001F970"
    "\U0001F971"
    "\U0001F973-\U0001F976"
    "\U0001F97A"
    "\U0001F97B"
    "\U0001F97C-\U0001F97F"
    "\U0001F980-\U0001F984"
    "\U0001F985-\U0001F991"
    "\U0001F992-\U0001F997"
    "\U0001F998-\U0001F9A2"
    "\U0001F9A5-\U0001F9AA"
    "\U0001F9AE-\U0001F9AF"
    "\U0001F9B0-\U0001F9B9"
    "\U0001F9BA-\U0001F9BF"
    "\U0001F9C0"
    "\U0001F9C1-\U0001F9C2"
    "\U0001F9C3-\U0001F9CA"
    "\U0001F9CD-\U0001F9CF"
    "\U0001F9D0-\U0001F9E6"
    "\U0001F9E7-\U0001F9FF"
    "\U0001FA70-\U0001FA73"
    "\U0001FA78-\U0001FA7A"
    "\U0001FA80-\U0001FA82"
    "\U0001FA90-\U0001FA95"
    "]"
)
TEXT_PRESENTATION_SELECTOR = "[\uFE0E]"
TEXT_PRESENTATION_SEQUENCE = f"(?:{EMOJI_CHARACTER}{TEXT_PRESENTATION_SELECTOR})"
EMOJI_PRESENTATION_SELECTOR = "[\uFE0F]"
EMOJI_PRESENTATION_SEQUENCE = f"(?:{EMOJI_CHARACTER}{EMOJI_PRESENTATION_SELECTOR})"
EMOJI_MODIFIER = "[\U0001F3FB-\U0001F3FF]"
EMOJI_MODIFIER_BASE = (
    "["
    "\u261D"
    "\u26F9"
    "\u270A-\u270D"
    "\U0001F385"
    "\U0001F3C2-\U0001F3C4"
    "\U0001F3C7"
    "\U0001F3CA-\U0001F3CC"
    "\U0001F442-\U0001F443"
    "\U0001F446-\U0001F450"
    "\U0001F466-\U0001F478"
    "\U0001F47C"
    "\U0001F481-\U0001F483"
    "\U0001F485-\U0001F487"
    "\U0001F48F"
    "\U0001F491"
    "\U0001F4AA"
    "\U0001F574-\U0001F575"
    "\U0001F57A"
    "\U0001F590"
    "\U0001F595-\U0001F596"
    "\U0001F645-\U0001F647"
    "\U0001F64B-\U0001F64F"
    "\U0001F6A3"
    "\U0001F6B4-\U0001F6B6"
    "\U0001F6C0"
    "\U0001F6CC"
    "\U0001F90F"
    "\U0001F918"
    "\U0001F919-\U0001F91E"
    "\U0001F91F"
    "\U0001F926"
    "\U0001F930"
    "\U0001F931-\U0001F932"
    "\U0001F933-\U0001F939"
    "\U0001F93C-\U0001F93E"
    "\U0001F9B5-\U0001F9B6"
    "\U0001F9B8-\U0001F9B9"
    "\U0001F9BB"
    "\U0001F9CD-\U0001F9CF"
    "\U0001F9D1-\U0001F9DD"
    "]"
)
EMOJI_MODIFIER_SEQUENCE = f"{EMOJI_MODIFIER_BASE}{EMOJI_MODIFIER}"
REGIONAL_INDICATOR = "[\U0001F1E6-\U0001F1FF]"
EMOJI_FLAG_SEQUENCE = f"{REGIONAL_INDICATOR}{2}"
TAG_BASE = f"(?:{EMOJI_MODIFIER_SEQUENCE}|{EMOJI_PRESENTATION_SEQUENCE}|{EMOJI_CHARACTER})"
TAG_SPEC = "[\U000E0020-\U000E007E]"
TAG_END = "\U000E007F"
EMOJI_TAG_SEQUENCE = f"(?:{TAG_BASE}{TAG_SPEC}{TAG_END})"
EMOJI_KEYCAP_SEQUENCE = "(?:[0-9#*]\uFE0F\u20E3)"
EMOJI_CORE_SEQUENCE = (
    f"(?:"
    f"{EMOJI_PRESENTATION_SEQUENCE}|"
    f"{EMOJI_KEYCAP_SEQUENCE}|"
    f"{EMOJI_MODIFIER_SEQUENCE}|"
    f"{EMOJI_FLAG_SEQUENCE}|"
    f"{EMOJI_CHARACTER}"
    f")"
)
EMOJI_ZWJ_ELEMENT = f"(?:{EMOJI_CORE_SEQUENCE}|{EMOJI_TAG_SEQUENCE})"
ZWJ = "\u200d"
EMOJI_ZWJ_SEQUENCE = f"(?:{EMOJI_ZWJ_ELEMENT}(?:{ZWJ}{EMOJI_ZWJ_ELEMENT})+)"

# http://www.unicode.org/reports/tr51/
# SMALL EDIT HERE: Added string start and end characters
EMOJI_SEQUENCE = f"^(?:{EMOJI_CORE_SEQUENCE}|{EMOJI_ZWJ_SEQUENCE}|{EMOJI_TAG_SEQUENCE})$"

EMOJI_REGEXP = re.compile(EMOJI_SEQUENCE)
