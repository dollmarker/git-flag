************************************************************
  1. ```
     # 扫描特定目录
     python doll.py -d "D:\CTF\challenge\.git"
     
     # 扫描并指定模式
     python doll.py -d "D:\CTF\challenge" -p "hack{.*}"
     (他会扫描hack{xxxx})
     
     # 安静模式扫描
     python doll.py -d "D:\CTF\challenge" -q
     
     
     指定.git目录：可以通过命令行参数指定要扫描的Git目录
     
     自动查找Git仓库：如果没有指定目录，会自动查找当前目录下的.git目录
     
     命令行参数支持：
     
     -d, --dir：指定.git目录或仓库目录
     
     -p, --pattern：直接指定搜索模式
     
     -f, --file：从文件读取搜索模式
     
     -q, --quiet：安静模式，不交互输入
     ```

     这个脚本可以自己找flag,  给ai写的，参考文章[Git泄漏找Flag思路总结 - CTF-Web修炼手册](https://wilesangh.github.io/ctf-web/Git泄漏找Flag思路总结/)

     ![](D:\CTFHU\信息收集\信息泄露\Git\自动找flag的脚本\屏幕截图 2026-01-08 234849.png)

     [![](D:\CTFHU\信息收集\信息泄露\Git\自动找flag的脚本\屏幕截图 2026-01-08 234855.png)
](https://github.com/dollmarker/git-flag/blob/main/%E8%87%AA%E5%8A%A8%E6%89%BEflag%E7%9A%84%E8%84%9A%E6%9C%AC/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202026-01-08%20234855.png)
     

     

     参考脚本如下：

     #!/bin/bash
     
     echo "[*] Git Repository Flag Hunter"
     echo "================================"

     1. Stash检查
     
     echo -e "\n[+] Checking stashes..."
     git stash list
     for i in {0..10}; do
         git stash show -p stash@{$i} 2>/dev/null | grep -i "flag\|ctf"
     done

     2. 提交历史检查
     
     echo -e "\n[+] Checking commit history..."
     git log --all --oneline | grep -i "flag\|add\|remove\|delete"

     3. Reflog检查
     
     echo -e "\n[+] Checking reflog..."
     git reflog | head -20

     4. 遍历所有提交查找flag
     
     echo -e "\n[+] Searching in all commits..."
     for commit in $(git log --all --format=%H); do
         git show $commit | grep -iE "flag\{|ctf\{|flag:" && echo "Found in: $commit"
     done

     5. 检查所有分支
     
     echo -e "\n[+] Checking all branches..."
     git branch -a

     6. 检查未引用对象
     
     echo -e "\n[+] Checking unreachable objects..."
     git fsck --unreachable

     7. 搜索所有对象
     
     echo -e "\n[+] Searching in all objects..."
     find .git/objects -type f | while read obj; do
         hash=$(echo $obj | sed 's/\.git\/objects\///g' | tr -d '/')
         git cat-file -p $hash 2>/dev/null | grep -iE "flag\{|ctf\{" && echo "Found in object: $hash"
     done

     echo -e "\n[*] Scan complete!"
     

     
