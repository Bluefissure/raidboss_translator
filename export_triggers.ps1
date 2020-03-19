Get-ChildItem "D:\Code\Git\cactbot\ui\raidboss\data\04-sb\" -Recurse -Filter *.js | 
Foreach-Object {
	echo Exporting $_.FullName
    python translator.py -f $_.FullName -e -rf response4.0.csv
}
