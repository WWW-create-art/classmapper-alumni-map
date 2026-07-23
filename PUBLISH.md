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
