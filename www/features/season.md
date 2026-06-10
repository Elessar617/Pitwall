# Season tracker

Everything you need between race weekends: the calendar, both championships,
results, and who's who — all cached locally so the app opens instantly and
survives flaky networks.

## Schedule

The full calendar with race, qualifying, and sprint times in UTC. The cursor
lands on the next race automatically.

<figure class="pitwall-shot" markdown>
![The schedule screen: a 22-round 2026 calendar table with circuits, locations, and session times, the cursor on the next upcoming round](../assets/schedule.svg)
</figure>

## Standings

Drivers' and constructors' championships, stacked in one view.

<figure class="pitwall-shot" markdown>
![The standings screen: the drivers championship table above the constructors table](../assets/standings.svg)
</figure>

## Results

Pick any round from the season list and the finishing order loads on demand —
grid position, laps, race time, status, and points per driver.

<figure class="pitwall-shot" markdown>
![The results screen: a rounds list beside the Monaco Grand Prix finishing order](../assets/results.svg)
</figure>

## Profiles

Driver and constructor rosters with numbers, codes, nationalities and birth
dates.

<figure class="pitwall-shot" markdown>
![The profiles screen: the driver roster table above the constructor roster](../assets/profiles.svg)
</figure>

!!! info "Cache-first by design"
    Season data comes from the Jolpica F1 API into a local SQLite cache. If a
    fetch fails, Pitwall serves the cached data and marks the subtitle
    `· stale` — no spinners, no blank screens.
