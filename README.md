# Advanced-Deduplication
Provides file level deduplication across selected directories in a reversible manner.

# Simple Guide
First download lastest Python version
 • or update to the latest https://www.python.org/downloads
Launch the program by double clicking on GUI.py file

# Benchmark
Two different versions of a video game, Crusader Kings 3 that is a quite challenging direcotry with many files and folders
|                    | Size (in bytes) | Files | Folders | Hash
|--------------------|-----------------|-------|---------|----------------------------------------------------------------------------------------------------------------         
| Hand Deduplicated: | 21,797,737,331  | 51371 | 5927    |
| Original:          | 26,451,925,804  | 66908 | 5742    | BLAKE2sp checksum for data and names: 2fba24b9bb76e26b6abc396cfc9f3155dd1e1366813255390961d2246fbd3ee8-00008D91
| Auto Deduplicated: | 15,689,201,160  | 43089 | 4478    |
| Auto Restoration:  | 26,451,925,804  | 66908 | 5742    | BLAKE2sp checksum for data and names: 2fba24b9bb76e26b6abc396cfc9f3155dd1e1366813255390961d2246fbd3ee8-00008D91

# Time it Took me
 • To deduplicate automatically: 2 minutes and 45 seconds
 • To restore automatically: 1 minute and 29 seconds

# Compression:
 • Hand Deduplicated: 42 minutes 27 seconds, output: 7.477MB
	
 • Audo Deduplicated: 1 hour 4 minutes and 4 seconds, output: 5,714,354,587
	
 • (Compression performed with LZMA2 with dicitionary size around 1380MB)

# My Computer Specs
 • CPU: Ryzen 5 3600
 • RAM: 16 GB
 • Storage: SSD

 # Google Meta Data
 <meta name="google-site-verification" content="GmZAeT-RmxdyYCQwbyPBe0RLw-tJz9QmbC7vBcGEeMY" />
