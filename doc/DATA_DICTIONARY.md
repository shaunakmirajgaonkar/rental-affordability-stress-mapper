# Data Dictionary

## Neighborhood metrics

`neighborhood_id` unique local identifier; `neighborhood_name` display name; `zone` local zone; `latitude` / `longitude` coordinates; `population` exposed population; `median_monthly_income` local median monthly income; `income_change_pct` recent income trend; `monthly_rent` typical monthly rent; `rent_growth_pct` recent rent trend; `monthly_utilities` typical monthly utilities; `monthly_commute_cost` typical monthly commuting cost; `average_commute_minutes` average commute duration.

## Cost history

`neighborhood_id`, `period`, `monthly_rent`, `monthly_utilities`, `monthly_commute_cost`, `monthly_income`.

History intentionally allows repeated `neighborhood_id` values because each neighborhood can have many time periods.
