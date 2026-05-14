# shanlu-nagoya.github.io

Personal academic website for Shan Lu, Nagoya University.

---

## Conference Tracker 更新说明

会议数据保存在 `update_conferences.py` 的 `CONFERENCES` 列表中，**纯手动维护，无爬虫**。

### 文件结构

```
update_conferences.py   ← 编辑这里来添加/修改会议
conferences/
  data.json             ← 由脚本生成，不要手动编辑
  index.html            ← 前端展示页面
```

### 会议分类（现有）

| Category | 包含会议 |
|---|---|
| Communications | ICC, GLOBECOM, WCNC, INFOCOM, ICCC, APCC, VTC |
| Information Theory | ISIT, ITW, ISITA |
| Optical Communications | OECC, ACP |
| ITS | IEEE IV |

### 如何添加一个新会议

在 `update_conferences.py` 的 `CONFERENCES` 列表里，按年份加入一条记录：

```python
{
    "name": "GLOBECOM 2028",                          # 显示名称（用于去重）
    "full_name": "IEEE Global Communications Conference",
    "organizer": "IEEE",                              # 主办方
    "category": "Communications",                    # 分类（见上表）
    "deadline": "2028-05-01",                        # 投稿截止日（YYYY-MM-DD，不知道填 None）
    "notification": None,
    "start": "2028-12-05",                           # 会议开始日
    "end":   "2028-12-09",                           # 会议结束日
    "location": "TBD",
    "url": "https://globecom2028.ieee-globecom.org/",
},
```

- 日期格式必须是 `"YYYY-MM-DD"` 或 `None`
- `deadline` 决定排序：有截止日的按截止日排序；`None` 排在最前面

### 更新步骤

```bash
# 1. 编辑脚本，添加/修改会议数据
# 打开 update_conferences.py，在 CONFERENCES 列表中增删记录

# 2. 运行脚本重新生成 data.json
python update_conferences.py

# 3. 提交并推送
git add update_conferences.py conferences/data.json
git commit -m "Update conference list: add XXXX 2028"
git push origin main
```

### 为什么改为手动维护？（2026-05-14）

原脚本通过爬虫抓取 vtsociety.org、itsoc.org、ieice.org，
但这些网站频繁返回 403 拒绝访问，导致 VTC、ITW、IEICE 会议大量丢失。
改为手动维护后更稳定，每次更新只需 3 步操作。
