# final_version
- dsl语法规则进一步完善，通过加入slots解决了存放订单号、投诉退款原因的问题
- 可实现三种场景的一步处理场景+原因和分步处理
- 添加test_unit mock测试桩和test_bot LLM脚本测试
- 添加了日志功能方便调试

# 使用说明
- 项目根目录运行main.py进入手动测试，运行test_unit.py进入mock测试，运行test_bot.py进入LLM脚本自动测试
- 注：因为test_bot的脚本测试有缺陷所以最后一个显示错误，对比实际输出其实是对的
- 其余功能详见项目文档


