# Profile Analysis Summary - KotorDiff Performance Bottlenecks

**Profile File:** tslpatchdata/test_kotordiff_profile.prof  
**Total Execution Time:** 433.20 seconds (~7.2 minutes)  
**Total Function Calls:** 589,862,000 calls

## Critical Bottlenecks Identified

### 1. 🔴 PRIMARY BOTTLENECK

[`resolve_resource_in_installation`](Libraries/PyKotor/src/pykotor/tslpatcher/diff/resolution.py#L86) - Resource Resolution

<<<<<<< Current (Your changes)
**Location:** [`resolution.py`](Libraries/PyKotor/src/pykotor/tslpatcher/diff/resolution.py):87  
=======

**Location:** [`resolution.py:87`](Libraries/PyKotor/src/pykotor/tslpatcher/diff/resolution.py#L87)  
>>>>>>> Incoming (Background Agent changes)
**Self Time:** 11.822 seconds  
**Cumulative Time:** 477.135 seconds (110% of total - includes subcalls)  
**Call Count:** 3,034 calls

**The Problem:**

- Called 3,033 times from `_diff_installations_with_resolution_impl`
- Inside each call, it's calling installation.**iter** **19,469,312 times total** (~6,414 iterations per call on average!)
- This suggests the `resource_index` optimization is NOT being used effectively, or there's a bug

**Root Cause Analysis:**
Looking at the code, there are two paths:

1. **Fast path (O(1)):** Uses `resource_index.get(identifier, [])` when index provided
2. **Slow path (O(n)):** Falls back to `[fr for fr in installation if fr.identifier() == identifier]`

The profile shows the slow path is being taken most of the time. Even though `build_resource_index()` is called and indices are passed to most calls, something is causing the fallback.

**Fix Required:**

1. **Verify `resource_index` is always passed** - Add logging/assertions
2. **Fix verbose logging calls** - Lines 913 and 967 call without `resource_index`
3. **Cache resolved resources** - Don't re-resolve the same identifier multiple times
4. **Ensure identifier comparisons are efficient** - The == check in the list comprehension calls `identifier()` which may be expensive

### 2. 🔴 SECONDARY BOTTLENECK: File I/O Operations

**{built-in method _io.open}:** 115,605 calls, **131.997 seconds** self time  
[**file.py:205(data)**](Libraries/PyKotor/src/pykotor/extract/file.py#L205): 105,900 calls, 142.350 seconds cumulative  
[**stream.py:135(from_file)**](Libraries/PyKotor/src/pykotor/common/stream.py#L135): 107,278 calls, 136.046 seconds cumulative

**The Problem:**

- Opening files 115K+ times is extremely expensive
- Many files are likely being opened multiple times (same file opened repeatedly)

**Fix Required:**

1. **Cache file data** - Don't re-read files that haven't changed
2. **Track file modification times** - Invalidate cache only when files change
3. **Batch file operations** - Read files once and reuse the data
4. **Use memory mapping** where possible for read-only access

### 3. 🔴 TERTIARY BOTTLENECK: Reference Cache Scanning

**
[`reference_cache.py`](Libraries/PyKotor/src/pykotor/tools/reference_cache.py):734([`find_all_strref_references`](Libraries/PyKotor/src/pykotor/tools/reference_cache.py#L758)):** 2 calls, **274.068 seconds** cumulative

- Calls file.py:205(data) 103,050 times (141.665 seconds)
- Calls
[`reference_cache.py`](Libraries/PyKotor/src/pykotor/tools/reference_cache.py):150([`scan_resource`](Libraries/PyKotor/src/pykotor/tools/reference_cache.py#L161)) 103,050 times (112.069 seconds)

**
[`reference_cache.py`](Libraries/PyKotor/src/pykotor/tools/reference_cache.py):230([`_scan_ncs`](Libraries/PyKotor/src/pykotor/tools/reference_cache.py#L241)):** 15,314 calls, **9.609 seconds** self time, 46.865 cumulative

- Reads byte-by-byte through NCS files (14M+ read_uint8 calls)

**The Problem:**

- Scanning every resource for string references is extremely expensive
- Same resources are scanned multiple times
- NCS files parsed byte-by-byte inefficiently

**Fix Required:**

1. **Cache scan results** - Don't re-scan unchanged resources
2. **Optimize NCS parsing** - Use bulk reads instead of byte-by-byte
3. **Parallelize scanning** - Scan independent resources in parallel
4. **Skip unnecessary scans** - Only scan resources that can contain string references

### 4. 🟡 Excessive Equality Comparisons

**ile.py:447(**eq**):** 20,128,505 calls, **17.293 seconds** self time  
Called primarily from
`resolve_resource_in_installation`

**The Problem:**

- 20M+ equality comparisons suggests inefficient lookups

**Fix Required:**

1. **Use hash-based lookups** - Convert to dict/set operations
2. **Cache comparison results** - Memoize **eq** calls
3. **Use identity checks first** -  is b before  == b

### 5. 🟡 Stream Reading Operations

[**stream.py:459(read_uint32)**](Libraries/PyKotor/src/pykotor/common/stream.py#L459): 15,013,179 calls, **18.263 seconds** self time  
[**stream.py:383(read_uint8)**](Libraries/PyKotor/src/pykotor/common/stream.py#L383): 15,417,646 calls, **16.845 seconds** self time  
[**stream.py:785(exceed_check)**](Libraries/PyKotor/src/pykotor/common/stream.py#L785): 50,356,178 calls, 8.089 seconds self time

**The Problem:**

- Excessive bounds checking (50M+ calls)
- Many small reads instead of bulk operations

**Fix Required:**

1. **Bulk read operations** - Read larger chunks at once
2. **Optimize bounds checking** - Cache or inline checks where possible
3. **Use memory-mapped files** for sequential reads

### 6. 🟡 INI Rewriting

**incremental_writer.py:2936(_rewrite_ini_complete):** 228 calls, **30.038 seconds** cumulative

- Called from `_write_gff_modification` (216 times)

**The Problem:**

- Rewriting the entire INI file 216 times is expensive

**Fix Required:**

1. **Batch writes** - Collect all modifications, write once at end
2. **Incremental updates** - Append to file instead of rewriting
3. **Delay writes** - Buffer modifications in memory

## Expected Overall Improvement

Implementing fixes #1-3 could reduce execution time from **433 seconds to ~130-200 seconds** (50-70% improvement).

## Immediate Action Items

1. **HIGH PRIORITY:** Fix `resolve_resource_in_installation` to always use `resource_index`
2. **HIGH PRIORITY:** Add file data caching
3. **MEDIUM PRIORITY:** Cache reference scan results
4. **MEDIUM PRIORITY:** Batch INI writes
5. **LOW PRIORITY:** Optimize stream reads and bounds checking
