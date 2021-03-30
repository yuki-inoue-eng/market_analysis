.DEFAULT_GOAL := help

.PHONY: fetch_candles
fetch_candles: ## fetch candles
ifndef i
	@bash -c "echo -e '\033[36mUsage: make fetch_candles i=USD_JPY t=2020-01-01 f=2021-01-01 g=1T\033[0m'"
else ifndef f
	@bash -c "echo -e '\033[36mUsage: make fetch_candles i=USD_JPY t=2020-01-01 f=2021-01-01 g=1T\033[0m'"
else ifndef t
	@bash -c "echo -e '\033[36mUsage: make fetch_candles i=USD_JPY t=2020-01-01 f=2021-01-01 g=1T\033[0m'"
else ifndef g
	@bash -c "echo -e '\033[36mUsage: make fetch_candles i=USD_JPY t=2020-01-01 f=2021-01-01 g=1T\033[0m'"
else
	ENV=Trade python ./fetch_candles_complement.py ${i} ${f} ${t} ${g}
endif

.PHONY: fetch_order_books
fetch_order_books: ## fetch order books
ifndef i
	@bash -c "echo -e '\033[36mUsage: make fetch_order_books i=USD_JPY t=2020-01-01 f=2021-01-01\033[0m'"
else ifndef f
	@bash -c "echo -e '\033[36mUsage: make fetch_order_books i=USD_JPY t=2020-01-01 f=2021-01-01\033[0m'"
else ifndef t
	@bash -c "echo -e '\033[36mUsage: make fetch_order_books i=USD_JPY t=2020-01-01 f=2021-01-01\033[0m'"
else
	ENV=Trade python ./fetch_order_books.py ${i} ${f} ${t}
endif

.PHONY: fetch_position_books
fetch_position_books: ## fetch position books
ifndef i
	@bash -c "echo -e '\033[36mUsage: make fetch_position_books i=USD_JPY t=2020-01-01 f=2021-01-01\033[0m'"
else ifndef f
	@bash -c "echo -e '\033[36mUsage: make fetch_position_books i=USD_JPY t=2020-01-01 f=2021-01-01\033[0m'"
else ifndef t
	@bash -c "echo -e '\033[36mUsage: make fetch_position_books i=USD_JPY t=2020-01-01 f=2021-01-01\033[0m'"
else
	ENV=Trade python ./fetch_position_books.py ${i} ${f} ${t}
endif

# See "Self-Documented Makefile" article
# https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
