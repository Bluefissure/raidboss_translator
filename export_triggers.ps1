Get-ChildItem "D:\Code\Git\cactbot\ui\raidboss\data\03-hw\" -Recurse -Filter *.js | 
Foreach-Object {
	echo Exporting $_.FullName
    python translator.py -f $_.FullName -e -rf response3.0.csv
}
