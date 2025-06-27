# vector_db.py
import json
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict
import re
from datetime import datetime

class JSONVectorDB:
    def __init__(self, db_path: str = "./json_db"):
        self.db_path = db_path
        self.index_file = os.path.join(db_path, "index.json")
        
        # 創建資料庫目錄
        os.makedirs(db_path, exist_ok=True)
        
        # 初始化或載入索引
        self.index = self._load_index()
    
    def _load_index(self) -> Dict:
        """載入索引文件"""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                print(f"警告: 索引文件損壞 ({e})，正在重新初始化...")
                # 備份損壞的文件
                backup_file = f"{self.index_file}.backup"
                if os.path.exists(self.index_file):
                    os.rename(self.index_file, backup_file)
                    print(f"已將損壞的索引文件備份為: {backup_file}")
                return {"documents": [], "metadata": {}}
            except Exception as e:
                print(f"讀取索引文件時發生未知錯誤: {e}")
                return {"documents": [], "metadata": {}}
        return {"documents": [], "metadata": {}}
    
    def _save_index(self):
        """保存索引文件（原子寫入）"""
        temp_file = f"{self.index_file}.tmp"
        try:
            # 先寫入臨時文件
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
            
            # 驗證寫入的文件是否有效
            with open(temp_file, 'r', encoding='utf-8') as f:
                json.load(f)  # 驗證 JSON 格式
            
            # 原子性替換
            os.replace(temp_file, self.index_file)
            
        except Exception as e:
            print(f"保存索引文件失敗: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise
    
    def _extract_timestamp(self, content: str) -> str:
        """從文本內容中提取時間戳"""
        if not content or not isinstance(content, str):
            return datetime.now().strftime('%Y%m%d')
            
        # 首先檢查是否包含 "編號與日期:" 模板
        if "編號與日期:" not in content:
            return datetime.now().strftime('%Y%m%d')
            
        # 尋找格式為 (數字) YYYYMMDD 的模式
        pattern = r'\(\d+\)\s*(\d{8})'
        match = re.search(pattern, content)
        if match:
            return match.group(1)
        return datetime.now().strftime('%Y%m%d')
    
    def add(self, ids: List[str], embeddings: List[List[float]], 
            documents: List[str], metadatas: List[Dict]):
        """添加文檔到資料庫"""
        for i in range(len(ids)):
            try:
                # 從文檔內容中提取時間戳
                timestamp = self._extract_timestamp(documents[i])
                
                # 確保文件名是字符串類型
                filename = str(metadatas[i].get("source", "unknown"))
                original_filename = str(metadatas[i].get("original_filename", os.path.basename(filename)))
                
                doc_data = {
                    "id": ids[i],
                    "filename": filename,
                    "original_filename": original_filename,
                    "content": documents[i],
                    "embedding": embeddings[i],
                    "metadata": metadatas[i],
                    "timestamp": timestamp
                }
                
                # 保存文檔到單獨的JSON文件
                doc_file = os.path.join(self.db_path, f"{ids[i]}.json")
                with open(doc_file, 'w', encoding='utf-8') as f:
                    json.dump(doc_data, f, ensure_ascii=False, indent=2)
                
                # 更新索引
                if not any(doc["id"] == ids[i] for doc in self.index["documents"]):
                    self.index["documents"].append({
                        "id": ids[i],
                        "filename": os.path.basename(filename),
                        "original_filename": original_filename,
                        "file_path": doc_file,
                        "timestamp": timestamp
                    })
                    self.index["metadata"][ids[i]] = metadatas[i]
            except Exception as e:
                print(f"處理文檔時發生錯誤: {str(e)}")
                continue
        
        self._save_index()
    
    def get(self, include: List[str] = None) -> Dict:
        """獲取所有文檔"""
        if include is None:
            include = ["documents", "metadatas", "ids"]
        
        result = {}
        documents = []
        metadatas = []
        ids = []
        embeddings = []
        
        for doc_info in self.index["documents"]:
            doc = self._get_document(doc_info["id"])
            if doc:
                ids.append(doc["id"])
                documents.append(doc["content"])
                # 將時間戳添加到元數據中
                metadata = doc["metadata"].copy()
                metadata["timestamp"] = doc["timestamp"]
                metadatas.append(metadata)
                embeddings.append(doc["embedding"])
        
        if "ids" in include:
            result["ids"] = ids
        if "documents" in include:
            result["documents"] = documents
        if "metadatas" in include:
            result["metadatas"] = metadatas
        if "embeddings" in include:
            result["embeddings"] = embeddings
        
        return result
    
    def _get_document(self, doc_id: str) -> Dict:
        """獲取特定文檔"""
        doc_file = os.path.join(self.db_path, f"{doc_id}.json")
        if os.path.exists(doc_file):
            with open(doc_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def query(self, query_embeddings: List[List[float]], n_results: int = 6) -> Dict:
        """向量相似度搜索"""
        query_vec = np.array(query_embeddings[0]).reshape(1, -1)
        results = []
        
        for doc_info in self.index["documents"]:
            doc = self._get_document(doc_info["id"])
            if doc and "embedding" in doc:
                doc_vec = np.array(doc["embedding"]).reshape(1, -1)
                similarity = cosine_similarity(query_vec, doc_vec)[0][0]
                distance = 1 - similarity
                results.append({
                    "document": doc["content"],
                    "metadata": doc["metadata"],
                    "distance": distance,
                    "id": doc["id"]
                })
        
        # 按距離排序
        results.sort(key=lambda x: x["distance"])
        results = results[:n_results]
        
        return {
            "documents": [[r["document"] for r in results]],
            "metadatas": [[r["metadata"] for r in results]],
            "distances": [[r["distance"] for r in results]],
            "ids": [[r["id"] for r in results]]
        }
    
    def delete_collection(self, name: str):
        """刪除集合（清空資料庫）"""
        for doc_info in self.index["documents"]:
            doc_file = os.path.join(self.db_path, f"{doc_info['id']}.json")
            if os.path.exists(doc_file):
                os.remove(doc_file)
        
        self.index = {"documents": [], "metadata": {}}
        self._save_index()

    def delete(self, ids: List[str]):
        """刪除指定的文檔"""
        # 創建要保留的文檔列表
        remaining_docs = []
        remaining_metadata = {}
        
        # 遍歷所有文檔
        for doc_info in self.index["documents"]:
            if doc_info["id"] not in ids:
                remaining_docs.append(doc_info)
                if doc_info["id"] in self.index["metadata"]:
                    remaining_metadata[doc_info["id"]] = self.index["metadata"][doc_info["id"]]
            else:
                # 刪除文檔文件
                doc_file = os.path.join(self.db_path, f"{doc_info['id']}.json")
                if os.path.exists(doc_file):
                    try:
                        os.remove(doc_file)
                    except Exception as e:
                        print(f"刪除文件 {doc_file} 時發生錯誤: {e}")
        
        # 更新索引
        self.index["documents"] = remaining_docs
        self.index["metadata"] = remaining_metadata
        
        # 保存更新後的索引
        self._save_index()
