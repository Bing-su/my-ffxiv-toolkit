.PHONY: fetch compare compare-npc compare-place

fetch:
	python main.py

compare:
	python compare.py

compare-npc:
	python compare.py -n

compare-place:
	python compare.py -p
