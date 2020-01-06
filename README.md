# every_coin_helps
1. ccxt (1.17.545)、python 3.6

2. 量化投资，主要使用bitfinex进行交易,也可换成其他ccxt支持的交易所。具体可参照ccxt开源项目

3. 账号设置在domain/my_exchange.py中，修改成自己的api-key[代码中为bitfinex示例key]。如使用vpn翻墙，则，需要使用proxies字段。

4.内含有多个策略，为自己研究开发，有借助boll线开发策略。重点开发back_return.py和bulin_K.py两个策略。

5.主要通过指令控制操作。同时通过邮件发送执行结果。替换代码中示例邮箱账号密码即可。
