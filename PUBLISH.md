# 发布到 GitHub Pages

1. 运行完整构建：

   ```bash
   bash scripts/build_all.sh
   ```

2. 把项目推送到你自己的 GitHub 仓库。

3. 在 GitHub 仓库页面打开 `Settings` -> `Pages`，确认 `Build and deployment` 的 `Source` 是 `GitHub Actions`。

4. 等 `Actions` 里的 `Deploy PWA to GitHub Pages` 运行完成，打开它给出的 Pages 地址。

5. 安卓 Chrome / iPhone Safari 打开这个 HTTPS 地址后，选择安装或添加到主屏幕。

## 管理员线上发布

网页里的“发布到线上”会把当前名单提交到 `data/jielong.csv`，然后 GitHub Actions 自动重新生成 GitHub Pages。发布时需要输入一次 GitHub token，这个 token 需要对 `WWW-create-art/classmapper-alumni-map` 仓库有 `Contents` 读写权限；网页不会保存 token。

注意：地图里包含同学姓名和学校，发布到 GitHub Pages 后通常是公开访问。

## 国内访问版本

如果同学在国内网络打不开 `github.io`，优先用 EdgeOne Makers/Pages 这类静态网站托管。当前项目已经把 Leaflet 地图库放进本地 `assets/vendor/leaflet/`，所以网页不再依赖国外 CDN；发布时只需要上传 `web-app` 目录即可。

### 方案 A：先免费直传，最快

1. 运行构建：

   ```bash
   bash scripts/build_all.sh
   bash scripts/package_web_app.sh
   ```

2. 打开 EdgeOne Makers/Pages 控制台，选择 Direct Upload / 直接上传。

3. 上传 `dist/classmapper-alumni-map-web-app.zip`。

4. 使用平台生成的 HTTPS 地址发给同学。

这个方案通常不需要买域名，也不需要先备案；缺点是管理员每次改完名单后，需要重新上传一次压缩包。

### 方案 B：接 Git 部署，后续自动更新

如果希望网页里“发布到线上”后国内版本也自动更新，就把 EdgeOne 项目连接到这个 GitHub 仓库，并配置构建：

```text
Install Command: python -m pip install -r requirements.txt
Build Command: python main.py data/jielong.csv --no-open --map-only && python scripts/build_pwa.py
Output Directory: web-app
```

管理员在网页发布名单后，会提交到 `data/jielong.csv`；GitHub Pages 和 EdgeOne 都应重新构建。这个方案更省心，但初次配置需要登录平台并授权 GitHub。

### 域名和备案

直接用平台分配的地址最省事。如果要绑定自己的 `.com` / `.cn` 域名，并希望在中国大陆正常访问，通常需要域名实名认证和备案；这一步可能会花钱，也会多一些等待时间。
