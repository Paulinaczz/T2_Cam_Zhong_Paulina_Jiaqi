/* Small source fixture for the metrics feasibility check. */
static int clamp_negative(int value)
{
    if (value < 0) {
        return 0; /* mixed code and comment */
    }
    return value;
}

int aggregate_positive(const int *values, int count)
{
    int total = 0;

    for (int index = 0; index < count; ++index) {
        total += clamp_negative(values[index]);
    }
    return total;
}
