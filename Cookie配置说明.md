# Cookie配置说明

**作者：五更琉璃**  
**日期：2025年**

## 为什么需要配置Cookie？

抖音爬虫需要有效的Cookie来模拟浏览器访问，获取数据。Cookie包含了用户的登录状态和身份验证信息。

## 如何获取Cookie？

### 方法一：从浏览器获取

1. **打开浏览器**，访问 `https://www.douyin.com`
2. **登录你的抖音账号**
3. **按F12**打开开发者工具
4. **切换到Network标签页**
5. **刷新页面**，找到任意一个请求
6. **点击请求**，在Request Headers中找到Cookie
7. **复制完整的Cookie值**

### 方法二：使用浏览器插件

1. 安装浏览器插件（如EditThisCookie）
2. 访问抖音网站并登录
3. 使用插件导出Cookie
4. 复制Cookie值

## 配置步骤

1. **编辑.env文件**
2. **将获取的Cookie值填入对应位置**：

```env
# 抖音主站Cookie（从www.douyin.com获取）
DOUYIN_COOKIE=你的完整Cookie值

# 直播间Cookie（从live.douyin.com获取）
LIVE_COOKIE=你的完整Cookie值
```

## 注意事项

1. **Cookie会过期**：通常几小时到几天就会失效，需要重新获取
2. **不要分享Cookie**：Cookie包含敏感信息，不要分享给他人
3. **定期更新**：建议每天或每次使用时都检查Cookie是否有效
4. **完整复制**：确保复制完整的Cookie值，不要遗漏任何部分

## 常见问题

### Q: Cookie获取后还是提示错误？
A: 检查以下几点：
- 确保已登录抖音账号
- 确保复制了完整的Cookie值
- 确保Cookie没有过期
- 确保.env文件格式正确

### Q: 如何判断Cookie是否有效？
A: 运行程序，如果提示"s_v_web_id"或"ttwid"错误，说明Cookie无效

### Q: Cookie多久会过期？
A: 通常几小时到几天，建议每次使用前都检查

### Q: 可以同时使用多个账号的Cookie吗？
A: 可以，但需要分别配置不同的.env文件

## 示例

正确的.env文件格式：

```env
# 抖音爬虫配置文件
# 作者：五更琉璃
# 日期：2025年

# 抖音主站Cookie（从www.douyin.com获取）
DOUYIN_COOKIE=msToken=xxx; ttwid=xxx; s_v_web_id=xxx; passport_csrf_token=xxx; ...

# 直播间Cookie（从live.douyin.com获取）
LIVE_COOKIE=msToken=xxx; ttwid=xxx; s_v_web_id=xxx; passport_csrf_token=xxx; ...

# 默认直播间ID
DEFAULT_LIVE_ID=19360448382
```

## 安全提醒

- 不要将包含Cookie的.env文件上传到公共代码仓库
- 定期更换Cookie
- 不要在公共网络环境下使用
- 遵守抖音的使用条款

---

**如有问题，请参考主README文件或联系开发者。**
