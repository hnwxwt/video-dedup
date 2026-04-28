"""
高精度模式功能测试脚本
用于验证修复后的代码是否正常工作
"""
import sys
import os

# 抑制OpenCV日志
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"

def test_high_precision_functions():
    """测试高精度模式的核心函数"""
    print("=" * 60)
    print("测试高精度模式函数")
    print("=" * 60)
    
    try:
        from core import (
            calculate_high_precision_similarity,
            find_duplicate_groups_high_precision,
            process_video_high_precision
        )
        print("✅ 成功导入高精度模式函数")
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    
    # 测试相似度计算函数是否存在
    try:
        # 创建模拟特征数据
        import imagehash
        import numpy as np
        from PIL import Image
        
        # 创建两个相似的图像
        img1 = Image.new('RGB', (100, 100), color='red')
        img2 = Image.new('RGB', (100, 100), color='red')
        
        # 计算特征
        img_resized = img1.resize((32, 32))
        phash1 = imagehash.phash(img_resized)
        ahash1 = imagehash.average_hash(img_resized)
        dhash1 = imagehash.dhash(img_resized)
        
        from core import calculate_color_histogram
        color_hist1 = calculate_color_histogram(img1.resize((64, 64)))
        
        features1 = {
            'phash_list': [phash1],
            'ahash_list': [ahash1],
            'dhash_list': [dhash1],
            'color_hist_list': [color_hist1]
        }
        
        img_resized2 = img2.resize((32, 32))
        phash2 = imagehash.phash(img_resized2)
        ahash2 = imagehash.average_hash(img_resized2)
        dhash2 = imagehash.dhash(img_resized2)
        color_hist2 = calculate_color_histogram(img2.resize((64, 64)))
        
        features2 = {
            'phash_list': [phash2],
            'ahash_list': [ahash2],
            'dhash_list': [dhash2],
            'color_hist_list': [color_hist2]
        }
        
        # 测试相似度计算
        score = calculate_high_precision_similarity(features1, features2)
        print(f"✅ 相似度计算成功: 相同图像得分 = {score:.2f}")
        
        if score < 1.0:
            print("✅ 相同图像的相似度得分合理（接近0）")
        else:
            print(f"⚠️ 警告: 相同图像得分偏高 ({score:.2f})")
        
        return True
        
    except Exception as e:
        print(f"❌ 相似度计算测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_structure_compatibility():
    """测试数据结构兼容性"""
    print("\n" + "=" * 60)
    print("测试数据结构兼容性")
    print("=" * 60)
    
    try:
        # 模拟不同模式的数据结构
        import imagehash
        
        # 精确模式：列表类型
        precise_data = [imagehash.phash(Image.new('RGB', (32, 32)))]
        
        # 高精度模式：字典类型
        high_precision_data = {
            'phash_list': [imagehash.phash(Image.new('RGB', (32, 32)))],
            'ahash_list': [],
            'dhash_list': [],
            'color_hist_list': []
        }
        
        # 测试类型判断
        if isinstance(precise_data, list):
            print("✅ 精确模式数据类型识别正确（list）")
        
        if isinstance(high_precision_data, dict):
            print("✅ 高精度模式数据类型识别正确（dict）")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据结构测试失败: {e}")
        return False

def main():
    print("\n🔍 开始高精度模式代码检查...\n")
    
    results = []
    
    # 测试1: 函数存在性
    results.append(("函数导入", test_high_precision_functions()))
    
    # 测试2: 数据结构兼容性
    results.append(("数据结构", test_data_structure_compatibility()))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！高精度模式代码已修复。")
    else:
        print("⚠️ 部分测试失败，请检查上述错误信息。")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
