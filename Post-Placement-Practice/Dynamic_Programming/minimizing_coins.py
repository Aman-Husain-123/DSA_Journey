def get_digits(num):
    digits = []
    while num > 0:
        d = num % 10
        if d != 0:
            digits.append(d)
        num //= 10
    return digits


n = int(input())

INF = float('inf')
dp = [INF] * (n + 1)

dp[0] = 0

for i in range(1, n + 1):
    for d in get_digits(i):
        dp[i] = min(dp[i], dp[i - d] + 1)

print(dp[n])