#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import os
import sys
import re
import argparse
import colorama
from colorama import Fore, Back, Style

# 初始化颜色输出
colorama.init(autoreset=True)

def run_git_command(cmd, git_dir=None):
    """运行Git命令并返回输出"""
    try:
        env = os.environ.copy()
        if git_dir:
            env['GIT_DIR'] = git_dir
        
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            encoding='utf-8', 
            errors='ignore',
            env=env
        )
        return result.stdout
    except Exception as e:
        return f"Error: {e}"

def change_to_git_parent_dir(git_dir):
    """切换到.git目录的父目录"""
    parent_dir = os.path.dirname(os.path.abspath(git_dir))
    try:
        os.chdir(parent_dir)
        print(f"{Fore.GREEN}✓ 已切换到目录: {parent_dir}")
        return True
    except Exception as e:
        print(f"{Fore.RED}✗ 无法切换到目录: {e}")
        return False

def find_git_directory(start_dir="."):
    """查找.git目录"""
    git_dir = os.path.abspath(start_dir)
    
    # 检查当前目录是否是.git目录
    if os.path.basename(git_dir) == ".git" and os.path.isdir(git_dir):
        return git_dir
    
    # 在当前目录中查找.git目录
    for root, dirs, files in os.walk(start_dir):
        if ".git" in dirs:
            git_path = os.path.join(root, ".git")
            if os.path.isdir(git_path):
                return git_path
    
    # 检查是否是bare仓库
    if os.path.exists(os.path.join(git_dir, "HEAD")):
        return git_dir
    
    return None

def print_section(title):
    """打印章节标题"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.YELLOW}[+] {title}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

def get_custom_patterns():
    """获取用户自定义的flag格式"""
    print(f"\n{Fore.MAGENTA}{'*'*60}")
    print(f"{Fore.CYAN}🔍 自定义Flag格式设置")
    print(f"{Fore.MAGENTA}{'*'*60}")
    
    # 默认的flag格式
    default_patterns = [
        r'flag\{[^}]*\}',      # flag{...}
        r'FLAG\{[^}]*\}',      # FLAG{...}
        r'ctf\{[^}]*\}',       # ctf{...}
        r'CTF\{[^}]*\}',       # CTF{...}
        r'key\{[^}]*\}',       # key{...}
    ]
    
    print(f"{Fore.YELLOW}默认搜索的flag格式:")
    for i, pattern in enumerate(default_patterns, 1):
        pattern_name = pattern.replace('\\', '')
        print(f"  {i}. {Fore.GREEN}{pattern_name}")
    
    print(f"\n{Fore.CYAN}是否要添加自定义flag格式? (y/n): ", end="")
    choice = input().strip().lower()
    
    custom_patterns = default_patterns.copy()
    
    if choice == 'y' or choice == 'yes':
        print(f"\n{Fore.YELLOW}请输入自定义flag格式:")
        print(f"{Fore.WHITE}格式说明:")
        print(f"  1. 使用 {{ 和 }} 表示花括号")
        print(f"  2. 使用正则表达式语法")
        print(f"  3. 例如: ctfhub{{.*}} 匹配 ctfhub{{xxx}}")
        print(f"  4. 例如: flag_.* 匹配 flag_xxx")
        print(f"  5. 输入 'done' 结束输入")
        print(f"{Fore.CYAN}{'-'*40}")
        
        while True:
            print(f"{Fore.GREEN}请输入自定义格式 (或输入 'done' 结束): ", end="")
            user_input = input().strip()
            
            if user_input.lower() == 'done':
                break
            
            if user_input:
                try:
                    # 测试正则表达式是否有效
                    re.compile(user_input)
                    custom_patterns.append(user_input)
                    print(f"{Fore.WHITE}  ✓ 已添加: {user_input}")
                except re.error as e:
                    print(f"{Fore.RED}  ✗ 无效的正则表达式: {e}")
    
    print(f"\n{Fore.CYAN}是否要搜索特定关键词? (y/n): ", end="")
    choice = input().strip().lower()
    
    if choice == 'y' or choice == 'yes':
        print(f"{Fore.YELLOW}请输入要搜索的关键词(用逗号分隔): ", end="")
        keywords = input().strip()
        if keywords:
            for keyword in keywords.split(','):
                keyword = keyword.strip()
                if keyword:
                    # 创建不区分大小写的关键词搜索模式
                    custom_patterns.append(f'{keyword}')
                    print(f"{Fore.WHITE}  ✓ 已添加关键词: {keyword}")
    
    print(f"\n{Fore.GREEN}✅ 最终搜索模式:")
    for i, pattern in enumerate(custom_patterns, 1):
        print(f"  {i}. {Fore.YELLOW}{pattern}")
    
    return custom_patterns

def find_flags_in_text(text, patterns, source=""):
    """在文本中查找匹配指定格式的flag"""
    flags = []
    found_in_source = []
    
    for pattern in patterns:
        try:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):  # 如果匹配到多个组
                    for item in match:
                        if item and item.strip():
                            clean_flag = item.strip()
                            if clean_flag not in flags:
                                flags.append(clean_flag)
                                found_in_source.append((clean_flag, pattern, source))
                else:
                    if match and match.strip():
                        clean_flag = match.strip()
                        if clean_flag not in flags:
                            flags.append(clean_flag)
                            found_in_source.append((clean_flag, pattern, source))
        except Exception as e:
            continue
    
    return flags, found_in_source

def search_in_location(location_name, git_cmd, patterns, git_dir=None, limit=None):
    """在指定位置搜索flag"""
    print(f"\n{Fore.WHITE}正在搜索: {Fore.CYAN}{location_name}")
    
    output = run_git_command(git_cmd, git_dir)
    if not output or "Error" in output or "fatal" in output:
        print(f"{Fore.YELLOW}  ⓘ  {location_name}为空或无结果")
        return [], []
    
    all_flags = []
    all_found = []
    
    if limit:
        lines = output.strip().split('\n')[:limit]
    else:
        lines = output.strip().split('\n')
    
    for i, line in enumerate(lines, 1):
        if not line:
            continue
        
        # 显示进度
        if len(lines) > 10:
            sys.stdout.write(f"\r{Fore.YELLOW}  进度: {i}/{len(lines)}")
            sys.stdout.flush()
        
        flags, found = find_flags_in_text(line, patterns, f"{location_name} 第{i}行")
        all_flags.extend(flags)
        all_found.extend(found)
    
    if len(lines) > 10:
        print()  # 换行
    
    return all_flags, all_found

def scan_git_repository(git_dir, patterns):
    """扫描指定的Git仓库"""
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.CYAN}🔍 开始扫描Git仓库")
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Git目录: {Fore.GREEN}{git_dir}")
    
    all_flags = []
    all_found_info = []
    
    # 1. 检查stash
    print_section("搜索stash...")
    stash_output = run_git_command("git stash list", git_dir)
    if stash_output:
        print(f"{Fore.WHITE}{stash_output}")
        
        for i in range(20):  # 检查stash@{0}到stash@{19}
            stash_cmd = f'git stash show -p stash@{{{i}}}'
            stash_content = run_git_command(stash_cmd, git_dir)
            if stash_content and "fatal" not in stash_content and "Error" not in stash_content:
                flags, found = find_flags_in_text(stash_content, patterns, f"stash@{{{i}}}")
                all_flags.extend(flags)
                all_found_info.extend(found)
    else:
        print(f"{Fore.YELLOW}没有stash")
    
    # 2. 检查提交信息
    print_section("搜索提交信息...")
    flags, found = search_in_location("提交信息", "git log --all --oneline", patterns, git_dir, 100)
    all_flags.extend(flags)
    all_found_info.extend(found)
    
    # 3. 检查提交内容
    print_section("深度搜索提交内容...")
    print(f"{Fore.YELLOW}这可能需要一些时间，请耐心等待...")
    
    commits_output = run_git_command("git log --all --format=%H", git_dir)
    if commits_output:
        commits = commits_output.strip().split('\n')
        if commits and commits[0]:
            print(f"{Fore.CYAN}总共有 {len(commits)} 个提交需要检查")
            print(f"{Fore.YELLOW}正在检查前 {min(30, len(commits))} 个提交...")
            
            for idx, commit in enumerate(commits[:30], 1):  # 限制检查前30个提交
                if commit:
                    sys.stdout.write(f"\r{Fore.YELLOW}进度: {idx}/{min(30, len(commits))} 个提交")
                    sys.stdout.flush()
                    
                    commit_content = run_git_command(f"git show {commit}", git_dir)
                    flags, found = find_flags_in_text(commit_content, patterns, f"提交 {commit[:8]}")
                    all_flags.extend(flags)
                    all_found_info.extend(found)
            
            print()  # 换行
    
    # 4. 检查当前文件
    print_section("搜索当前文件...")
    grep_cmd = 'git grep -i "flag\|ctf\|key" -- "*" 2>/dev/null || git grep "flag\|ctf\|key" -- "*"'
    flags, found = search_in_location("当前文件", grep_cmd, patterns, git_dir, 50)
    all_flags.extend(flags)
    all_found_info.extend(found)
    
    # 5. 检查所有提交的文件内容
    print_section("搜索所有历史文件...")
    print(f"{Fore.YELLOW}正在搜索所有提交中的文件内容...")
    
    grep_all_cmd = 'git log -p --all -S"flag" 2>/dev/null || echo "无法执行深度搜索"'
    flags, found = search_in_location("历史文件", grep_all_cmd, patterns, git_dir, 100)
    all_flags.extend(flags)
    all_found_info.extend(found)
    
    # 6. 检查reflog
    print_section("搜索reflog...")
    flags, found = search_in_location("reflog", "git reflog", patterns, git_dir, 30)
    all_flags.extend(flags)
    all_found_info.extend(found)
    
    # 7. 检查分支
    print_section("检查分支...")
    branches_output = run_git_command("git branch -a", git_dir)
    if branches_output:
        print(f"{Fore.WHITE}{branches_output}")
    
    # 8. 检查未引用对象
    print_section("搜索未引用对象...")
    fsck_output = run_git_command("git fsck --unreachable", git_dir)
    if fsck_output and "unreachable" in fsck_output:
        print(f"{Fore.RED}发现未引用对象，正在检查...")
        
        for line in fsck_output.split('\n'):
            if 'unreachable' in line and 'commit' in line:
                obj_hash = line.split()[2]
                obj_content = run_git_command(f"git cat-file -p {obj_hash}", git_dir)
                flags, found = find_flags_in_text(obj_content, patterns, f"未引用对象 {obj_hash}")
                all_flags.extend(flags)
                all_found_info.extend(found)
    else:
        print(f"{Fore.YELLOW}没有未引用对象")
    
    return all_flags, all_found_info

def display_results(all_flags, all_found_info, patterns, git_dir):
    """显示扫描结果"""
    print_section("扫描结果")
    
    if all_flags:
        # 去重
        unique_flags = []
        unique_found_info = []
        
        for flag, info in zip(all_flags, all_found_info):
            if flag not in unique_flags:
                unique_flags.append(flag)
                unique_found_info.append(info)
        
        print(f"{Fore.GREEN}🎉 共发现 {len(unique_flags)} 个唯一匹配项:")
        print(f"{Fore.CYAN}{'='*80}")
        
        # 按来源分组显示
        flags_by_source = {}
        for flag, (flag_text, pattern, source) in zip(unique_flags, unique_found_info):
            if source not in flags_by_source:
                flags_by_source[source] = []
            flags_by_source[source].append((flag, pattern))
        
        for source, flags_list in flags_by_source.items():
            print(f"\n{Fore.YELLOW}📁 来源: {Fore.CYAN}{source}")
            for flag, pattern in flags_list:
                print(f"  {Fore.GREEN}✓ {Fore.RED}{flag}")
                print(f"    匹配模式: {Fore.WHITE}{pattern}")
        
        print(f"{Fore.CYAN}{'='*80}")
        
        # 保存到文件
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 使用Git目录名作为文件名一部分
        git_dir_name = os.path.basename(os.path.dirname(git_dir)) if git_dir.endswith('.git') else os.path.basename(git_dir)
        filename = f"found_flags_{git_dir_name}_{timestamp}.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"扫描时间: {timestamp}\n")
            f.write(f"Git目录: {git_dir}\n")
            f.write(f"搜索模式: {patterns}\n")
            f.write(f"共找到 {len(unique_flags)} 个匹配项\n")
            f.write("="*60 + "\n\n")
            
            for source, flags_list in flags_by_source.items():
                f.write(f"\n来源: {source}\n")
                f.write("-"*40 + "\n")
                for flag, pattern in flags_list:
                    f.write(f"✓ {flag}\n")
                    f.write(f"  匹配模式: {pattern}\n")
        
        print(f"{Fore.GREEN}✅ 结果已保存到: {Fore.WHITE}{filename}")
        
        # 显示统计信息
        print(f"\n{Fore.CYAN}📊 统计信息:")
        print(f"  {Fore.WHITE}总匹配数: {Fore.YELLOW}{len(unique_flags)}")
        print(f"  {Fore.WHITE}搜索位置数: {Fore.YELLOW}{len(flags_by_source)}")
        print(f"  {Fore.WHITE}搜索模式数: {Fore.YELLOW}{len(patterns)}")
        print(f"  {Fore.WHITE}Git目录: {Fore.YELLOW}{git_dir}")
        
        # 按模式统计
        pattern_counts = {}
        for _, pattern, _ in all_found_info:
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        print(f"\n{Fore.CYAN}🔍 匹配模式统计:")
        for pattern, count in pattern_counts.items():
            pattern_display = pattern.replace('\\', '')[:50]
            print(f"  {Fore.WHITE}{pattern_display}: {Fore.YELLOW}{count}次")
    
    else:
        print(f"{Fore.RED}😔 没有找到匹配项")
        print(f"{Fore.YELLOW}尝试:")
        print(f"  1. 检查flag格式是否正确")
        print(f"  2. 尝试更简单的搜索模式")
        print(f"  3. 检查其他分支")
        print(f"  4. 尝试搜索不同的关键词")

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Git仓库Flag扫描工具')
    parser.add_argument('-d', '--dir', help='指定.git目录或仓库目录')
    parser.add_argument('-p', '--pattern', help='直接指定搜索模式（正则表达式）')
    parser.add_argument('-f', '--file', help='从文件读取搜索模式（每行一个正则表达式）')
    parser.add_argument('-q', '--quiet', action='store_true', help='安静模式，不交互输入')
    args = parser.parse_args()
    
    git_dir = args.dir
    custom_patterns = []
    
    # 查找或验证Git目录
    if git_dir:
        git_dir = os.path.abspath(git_dir)
        if os.path.isdir(git_dir):
            if os.path.basename(git_dir) != ".git":
                # 检查是否包含.git子目录
                git_subdir = os.path.join(git_dir, ".git")
                if os.path.isdir(git_subdir):
                    git_dir = git_subdir
                else:
                    # 检查是否是bare仓库
                    if not os.path.exists(os.path.join(git_dir, "HEAD")):
                        print(f"{Fore.RED}[!] 错误: {git_dir} 不是有效的Git仓库目录")
                        print(f"{Fore.YELLOW}请指定包含.git的目录或.git目录本身")
                        sys.exit(1)
    else:
        # 自动查找.git目录
        git_dir = find_git_directory(".")
        if not git_dir:
            print(f"{Fore.RED}[!] 错误: 当前目录不是Git仓库")
            print(f"{Fore.YELLOW}请使用 -d 参数指定Git目录")
            sys.exit(1)
    
    print(f"\n{Fore.MAGENTA}{'*'*60}")
    print(f"{Fore.CYAN}🎯 Git Repository Flag Hunter - 高级版")
    print(f"{Fore.MAGENTA}{'*'*60}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Git目录: {Fore.GREEN}{git_dir}")
    
    # 获取搜索模式
    if args.pattern:
        # 从命令行参数获取模式
        custom_patterns = [args.pattern]
        print(f"{Fore.GREEN}使用命令行模式: {args.pattern}")
    elif args.file:
        # 从文件读取模式
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                for line in f:
                    pattern = line.strip()
                    if pattern and not pattern.startswith('#'):
                        try:
                            re.compile(pattern)
                            custom_patterns.append(pattern)
                        except re.error:
                            print(f"{Fore.YELLOW}警告: 跳过无效的正则表达式: {pattern}")
            print(f"{Fore.GREEN}从文件加载了 {len(custom_patterns)} 个搜索模式")
        except Exception as e:
            print(f"{Fore.RED}错误: 无法读取模式文件: {e}")
            sys.exit(1)
    elif not args.quiet:
        # 交互式输入
        custom_patterns = get_custom_patterns()
    else:
        # 安静模式，使用默认模式
        custom_patterns = [
            r'flag\{[^}]*\}',
            r'FLAG\{[^}]*\}',
            r'ctf\{[^}]*\}',
            r'CTF\{[^}]*\}',
            r'key\{[^}]*\}',
        ]
        print(f"{Fore.GREEN}使用默认搜索模式")
    
    # 切换到Git仓库的父目录
    original_dir = os.getcwd()
    if not change_to_git_parent_dir(git_dir):
        print(f"{Fore.YELLOW}警告: 无法切换到Git目录，尝试在当前目录扫描")
    
    try:
        # 扫描Git仓库
        all_flags, all_found_info = scan_git_repository(git_dir, custom_patterns)
        
        # 显示结果
        display_results(all_flags, all_found_info, custom_patterns, git_dir)
        
    finally:
        # 切换回原始目录
        os.chdir(original_dir)
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.GREEN}[*] 扫描完成!")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    if not args.quiet and not args.pattern and not args.file:
        print(f"\n{Fore.YELLOW}是否要用其他格式重新搜索? (y/n): ", end="")
        if input().strip().lower() in ['y', 'yes']:
            main()  # 重新开始

if __name__ == "__main__":
    # 检查是否安装了git
    try:
        subprocess.run("git --version", shell=True, check=True, capture_output=True)
    except:
        print(f"{Fore.RED}[!] 错误: 未找到Git，请先安装Git for Windows")
        print(f"{Fore.YELLOW}从 https://git-scm.com/download/win 下载并安装")
        sys.exit(1)
    
    # 检查是否安装了colorama
    try:
        import colorama
    except ImportError:
        print(f"{Fore.YELLOW}[!] 正在安装colorama库...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "colorama"])
        import colorama
        from colorama import Fore, Back, Style
        colorama.init(autoreset=True)
    
    main()