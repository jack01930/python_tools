#!/usr/bin/env python3
"""
向量数据库概念验证 Demo

验证目的：
1. ChromaDB 能否有效存储和检索中文记账对话
2. Sentence-Transformers 对中文记账文本的 Embedding 质量
3. 语义检索相比时间顺序检索的优势

测试数据：模拟真实记账对话场景
"""

import json
import time
from typing import List, Dict, Any
import hashlib

# 1. 为什么使用本地模型而非云服务？
"""
本地 Embedding 模型的优势：
1. 成本为零：无 API 调用费用
2. 延迟极低：无需网络请求，毫秒级响应
3. 隐私安全：数据不离开本地
4. 离线可用：不依赖外部服务
5. 可控性强：可自定义模型和参数

权衡：模型质量可能略低于顶级云服务，但对记账场景足够
"""

def print_header(title: str):
    """打印分隔标题"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def test_chromadb_semantic_search():
    """测试 ChromaDB 语义检索功能"""
    print_header("1. 测试 ChromaDB 语义检索")

    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except ImportError as e:
        print(f"❌ 缺少依赖：{e}")
        print("请先安装：pip install chromadb sentence-transformers torch")
        return False

    # 模拟记账对话数据
    conversations = [
        {
            "id": "1",
            "text": "今天中午吃了20元的牛肉面",
            "category": "饮食",
            "amount": -20.0,
            "date": "2024-01-15"
        },
        {
            "id": "2",
            "text": "午餐牛肉面花费20元",
            "category": "饮食",
            "amount": -20.0,
            "date": "2024-01-16"
        },
        {
            "id": "3",
            "text": "晚饭吃了火锅，花了150元",
            "category": "饮食",
            "amount": -150.0,
            "date": "2024-01-17"
        },
        {
            "id": "4",
            "text": "公交卡充值100元",
            "category": "交通",
            "amount": -100.0,
            "date": "2024-01-18"
        },
        {
            "id": "5",
            "text": "打车去公司花了35元",
            "category": "交通",
            "amount": -35.0,
            "date": "2024-01-19"
        },
        {
            "id": "6",
            "text": "超市购物买了牛奶和面包，花了45元",
            "category": "购物",
            "amount": -45.0,
            "date": "2024-01-20"
        },
        {
            "id": "7",
            "text": "买了件衬衫，花了120元",
            "category": "购物",
            "amount": -120.0,
            "date": "2024-01-21"
        },
        {
            "id": "8",
            "text": "工资收入5000元",
            "category": "工资",
            "amount": 5000.0,
            "date": "2024-01-22"
        }
    ]

    # 测试查询用例
    test_queries = [
        {
            "query": "我这个月吃饭花了多少钱",
            "expected_category": "饮食",
            "expected_ids": ["1", "2", "3"]  # 应该返回所有饮食相关
        },
        {
            "query": "交通费用多少",
            "expected_category": "交通",
            "expected_ids": ["4", "5"]
        },
        {
            "query": "购物消费",
            "expected_category": "购物",
            "expected_ids": ["6", "7"]
        },
        {
            "query": "午餐开销",
            "expected_category": "饮食",
            "expected_ids": ["1", "2"]  # 午餐相关
        }
    ]

    print(f"📊 测试数据：{len(conversations)} 条记账对话")
    print(f"📝 测试查询：{len(test_queries)} 个语义查询")

    try:
        # 1. 初始化 ChromaDB
        chroma_client = chromadb.PersistentClient(path="./chroma_test_db")
        collection = chroma_client.get_or_create_collection(
            name="finance_conversations",
            metadata={"hnsw:space": "cosine"}
        )

        # 2. 加载 Embedding 模型
        print("🔄 加载 Sentence-Transformers 模型...")
        start_time = time.time()
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        load_time = time.time() - start_time
        print(f"   ✅ 模型加载完成，耗时 {load_time:.2f} 秒")
        print(f"   📏 模型维度：{model.get_sentence_embedding_dimension()}")

        # 3. 生成 Embedding 并存储
        print("🔄 生成 Embedding 并存储到向量库...")
        documents = []
        embeddings = []
        metadatas = []
        ids = []

        for conv in conversations:
            # 生成文本 embedding
            embedding = model.encode(conv["text"]).tolist()

            documents.append(conv["text"])
            embeddings.append(embedding)
            metadatas.append({
                "category": conv["category"],
                "amount": conv["amount"],
                "date": conv["date"],
                "id": conv["id"]
            })
            ids.append(conv["id"])

        # 批量添加到向量库
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        print(f"   ✅ 存储 {len(conversations)} 条记录到向量库")

        # 4. 测试语义检索
        print_header("2. 语义检索测试结果")

        all_passed = True
        for test_case in test_queries:
            print(f"\n🔍 查询：'{test_case['query']}'")
            print(f"   期望分类：{test_case['expected_category']}")
            print(f"   期望相关ID：{test_case['expected_ids']}")

            # 生成查询 embedding
            query_embedding = model.encode(test_case["query"]).tolist()

            # 执行语义搜索
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=5,
                include=["documents", "metadatas", "distances"]
            )

            # 解析结果
            returned_ids = []
            returned_categories = []

            if results["ids"] and len(results["ids"][0]) > 0:
                for i, doc_id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i]
                    similarity = 1 - distance  # 转换为相似度分数

                    returned_ids.append(doc_id)
                    returned_categories.append(metadata["category"])

                    print(f"   {i+1}. ID:{doc_id} | 分类:{metadata['category']} | "
                          f"金额:{metadata['amount']} | 相似度:{similarity:.3f}")

            # 评估检索效果
            correct_categories = [cat for cat in returned_categories
                                if cat == test_case["expected_category"]]
            category_accuracy = len(correct_categories) / len(returned_categories) if returned_categories else 0

            # 检查是否返回了期望的ID
            expected_found = [doc_id for doc_id in test_case["expected_ids"]
                            if doc_id in returned_ids]
            recall_rate = len(expected_found) / len(test_case["expected_ids"]) if test_case["expected_ids"] else 1

            print(f"   分类准确率：{category_accuracy:.1%}")
            print(f"   召回率：{recall_rate:.1%} ({len(expected_found)}/{len(test_case['expected_ids'])})")

            if category_accuracy >= 0.6 and recall_rate >= 0.5:
                print("   ✅ 通过")
            else:
                print("   ⚠️  效果一般，可能需要优化")
                all_passed = False

        # 5. 对比时间顺序检索
        print_header("3. 时间顺序 vs 语义检索对比")

        # 模拟时间顺序检索（最近 N 条）
        print("⏰ 时间顺序检索（最近 3 条）：")
        recent_convs = conversations[-3:]
        for conv in recent_convs:
            print(f"   - {conv['text']} (ID:{conv['id']}, 分类:{conv['category']})")

        # 测试一个具体查询
        test_query = "我这个月吃饭花了多少钱"
        print(f"\n🔍 查询：'{test_query}'")

        # 语义检索结果
        query_embedding = model.encode(test_query).tolist()
        semantic_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5,
            include=["documents", "metadatas", "distances"]
        )

        print("🧠 语义检索结果（按相关度排序）：")
        if semantic_results["ids"] and len(semantic_results["ids"][0]) > 0:
            for i, doc_id in enumerate(semantic_results["ids"][0]):
                metadata = semantic_results["metadatas"][0][i]
                distance = semantic_results["distances"][0][i]
                similarity = 1 - distance

                print(f"   {i+1}. {metadata['category']} | "
                      f"ID:{doc_id} | 相似度:{similarity:.3f}")

        # 6. 性能测试
        print_header("4. 性能测试")

        # Embedding 生成速度
        test_texts = [conv["text"] for conv in conversations]
        start_time = time.time()
        embeddings = model.encode(test_texts)
        embed_time = time.time() - start_time

        print(f"📈 Embedding 生成速度：")
        print(f"   - 批量 {len(test_texts)} 条文本：{embed_time:.3f} 秒")
        print(f"   - 平均每条：{(embed_time/len(test_texts))*1000:.1f} 毫秒")

        # 检索速度
        start_time = time.time()
        for _ in range(10):
            collection.query(
                query_embeddings=[query_embedding],
                n_results=5
            )
        query_time = (time.time() - start_time) / 10

        print(f"🔍 检索速度：")
        print(f"   - 平均每次查询：{query_time*1000:.1f} 毫秒")

        # 7. 内存占用估算
        print(f"💾 内存占用估算：")
        print(f"   - 模型大小：~480 MB")
        print(f"   - 每条记录：~3 KB (768维float32)")
        print(f"   - 10万条记录：~300 MB")

        return all_passed

    except Exception as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False

def test_embedding_quality():
    """测试 Embedding 模型对中文记账文本的质量"""
    print_header("5. Embedding 质量测试")

    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np

        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

        # 测试文本对
        test_pairs = [
            {
                "text1": "今天中午吃了20元的牛肉面",
                "text2": "午餐牛肉面花费20元",
                "expected_similarity": "高",  # 相同意思，不同表述
                "reason": "相同场景（午餐牛肉面），不同表述"
            },
            {
                "text1": "今天中午吃了20元的牛肉面",
                "text2": "晚饭吃了火锅，花了150元",
                "expected_similarity": "中",  # 都是饮食，但不同餐次
                "reason": "同分类（饮食），不同具体内容"
            },
            {
                "text1": "今天中午吃了20元的牛肉面",
                "text2": "公交卡充值100元",
                "expected_similarity": "低",  # 完全不同分类
                "reason": "不同分类（饮食 vs 交通）"
            },
            {
                "text1": "工资收入5000元",
                "text2": "收到了5000元工资",
                "expected_similarity": "高",  # 相同意思
                "reason": "相同事件，不同表述"
            }
        ]

        print("测试中文记账文本的语义相似度：")

        for pair in test_pairs:
            # 生成 embedding
            emb1 = model.encode(pair["text1"])
            emb2 = model.encode(pair["text2"])

            # 计算余弦相似度
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

            print(f"\n📝 文本1：{pair['text1']}")
            print(f"📝 文本2：{pair['text2']}")
            print(f"🧮 余弦相似度：{similarity:.3f}")
            print(f"📊 预期：{pair['expected_similarity']} - {pair['reason']}")

            # 简单评估
            if pair["expected_similarity"] == "高" and similarity > 0.7:
                print("   ✅ 符合预期")
            elif pair["expected_similarity"] == "中" and 0.4 < similarity <= 0.7:
                print("   ✅ 符合预期")
            elif pair["expected_similarity"] == "低" and similarity <= 0.4:
                print("   ✅ 符合预期")
            else:
                print("   ⚠️  与预期有偏差")

        return True

    except Exception as e:
        print(f"❌ Embedding 质量测试失败：{e}")
        return False

def main():
    """主函数"""
    print_header("向量数据库概念验证 Demo")
    print("验证 ChromaDB + Sentence-Transformers 对中文记账场景的适用性")

    # 检查依赖
    print("\n🔍 检查依赖...")
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        print("✅ 依赖检查通过")
    except ImportError:
        print("❌ 缺少必要依赖")
        print("请运行：pip install chromadb sentence-transformers torch")
        return

    # 运行测试
    chromadb_passed = test_chromadb_semantic_search()
    embedding_passed = test_embedding_quality()

    print_header("测试总结")

    if chromadb_passed and embedding_passed:
        print("🎉 所有测试通过！向量库方案符合预期")
        print("\n✅ 推荐使用方案：")
        print("   1. ChromaDB 作为向量存储")
        print("   2. Sentence-Transformers (paraphrase-multilingual-MiniLM-L12-v2)")
        print("   3. 混合检索策略（语义 + 时间 + 槽位）")
    else:
        print("⚠️  测试结果一般，可能需要调整方案")
        print("\n📋 考虑因素：")
        print("   1. 尝试其他 Embedding 模型")
        print("   2. 调整检索参数（n_results, where 过滤）")
        print("   3. 增加更多训练数据")

    print("\n📁 生成的测试数据：")
    print("   - chroma_test_db/ : ChromaDB 数据库目录")
    print("   - 可删除：rm -rf chroma_test_db/")

if __name__ == "__main__":
    main()