"""Google style OKR grading helpers (0.0 - 1.0)."""

# Score bands: red < 0.4 <= yellow < 0.7 <= green
BAND_YELLOW = 0.4
BAND_GREEN = 0.7
BANDS = ('red', 'yellow', 'green')
# Expected score per objective type
TYPE_TARGETS = {'committed': 1.0, 'aspirational': 0.7}
# Early in the cycle projections are noisy: the elapsed time used to project is floored at 25 %.
MIN_ELAPSED_FOR_PROJECTION = 25.0


def score_band(score):
    score = score or 0.0
    if score < BAND_YELLOW:
        return 'red'
    if score < BAND_GREEN:
        return 'yellow'
    return 'green'


def average(values, digits=2):
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), digits) if values else 0.0
