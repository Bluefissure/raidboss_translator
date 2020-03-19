Get-ChildItem "D:\Code\Git\cactbot\ui\raidboss\data\05-shb\" -Recurse -Filter *.js | 
Foreach-Object {
	echo Translating $_.FullName
    python translator.py -f $_.FullName -rf response5.0.csv
}