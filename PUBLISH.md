# 发布到 GitHub Pages

1. 运行完整构建：

   ```bash
   bash scripts/build_all.sh
   ```

2. 把项目推送到你自己的 GitHub 仓库。

3. 在 GitHub 仓库页面打开 `Settings` -> `Pages`，确认 `Build and deployment` 的 `Source` 是 `GitHub Actions`。

4. 等 `Actions` 里的 `Deploy PWA to GitHub Pages` 运行完成，打开它给出的 Pages 地址。

5. 安卓 Chrome / iPhone Safari 打开这个 HTTPS 地址后，选择安装或添加到主屏幕。

注意：地图里包含同学姓名和学校，发布到 GitHub Pages 后通常是公开访问。
