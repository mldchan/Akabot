from utils.generic import pretty_time_delta

for no_seconds in [True, False]:
    for no_minutes in [True, False]:
        delta_1 = pretty_time_delta(59, 0, 0, show_seconds=no_seconds, show_minutes=no_minutes)
        print(f"show_seconds={no_seconds}, show_minutes={no_minutes}: {delta_1}")

        delta_2 = pretty_time_delta(60, 0, 0, show_seconds=no_seconds, show_minutes=no_minutes)
        print(f"show_seconds={no_seconds}, show_minutes={no_minutes}: {delta_2}")

        delta_3 = pretty_time_delta(3599, 0, 0, show_seconds=no_seconds, show_minutes=no_minutes)
        print(f"show_seconds={no_seconds}, show_minutes={no_minutes}: {delta_3}")

        delta_4 = pretty_time_delta(3600, 0, 0, show_seconds=no_seconds, show_minutes=no_minutes)
        print(f"show_seconds={no_seconds}, show_minutes={no_minutes}: {delta_4}")

        delta_5 = pretty_time_delta(86400, 0, 0, show_seconds=no_seconds, show_minutes=no_minutes)
        print(f"show_seconds={no_seconds}, show_minutes={no_minutes}: {delta_5}")