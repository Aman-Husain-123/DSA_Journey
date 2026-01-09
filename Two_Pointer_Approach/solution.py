arr = [1]
nums = sorted(arr)

# Check if the array is already sorted
if arr == nums:
    print(0)
else:
    # Find the first index where elements differ
    for i in range(len(arr)):
        if arr[i] != nums[i]:
            small = i
            break

    # Find the last index where elements differ
    for j in range(len(arr)-1, -1, -1):
        if arr[j] != nums[j]:
            large = j
            break

    # Calculate the length of the unsorted subarray
    print(large - small + 1)
