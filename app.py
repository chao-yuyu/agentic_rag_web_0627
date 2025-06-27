from flask import Flask, render_template, request, jsonify, Response
import os
from werkzeug.utils import secure_filename
from agent_rag_0609 import CustomRAGAgentSystem
import uuid
import json
import time
import threading
import subprocess
import tempfile
import glob
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 修改任務管理系統：按IP分組
# 結構: {ip: {task_id: task_data}}
running_tasks_by_ip = {}
task_lock = threading.Lock()

# 全局變量用於保存已完成的任務的篩選交互訊息
completed_task_interactions = {}
completed_task_lock = threading.Lock()

# 確保上傳目錄存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化RAG系統
rag_system = CustomRAGAgentSystem(reset_db=False, db_path="./custom_json_rag_db")

# 允許的文件類型
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'md', 'json', 'docx', 'doc', 'xlsx', 'xls'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_sse(data: str, event=None) -> str:
    """格式化 SSE 數據"""
    msg = f'data: {data}\n\n'
    if event is not None:
        msg = f'event: {event}\n{msg}'
    return msg

def get_client_ip():
    """獲取客戶端IP地址"""
    # 檢查是否有代理
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def cleanup_expired_tasks():
    """清理過期的已完成任務（保留1小時）"""
    current_time = time.time()
    expired_tasks = []
    
    with completed_task_lock:
        for task_id, task_data in completed_task_interactions.items():
            if current_time - task_data['completed_time'] > 3600:  # 1小時後過期
                expired_tasks.append(task_id)
        
        for task_id in expired_tasks:
            del completed_task_interactions[task_id]
    
    if expired_tasks:
        print(f"清理了 {len(expired_tasks)} 個過期任務")

def cleanup_ip_tasks(ip):
    """清理指定IP的所有正在執行的任務"""
    with task_lock:
        if ip in running_tasks_by_ip:
            for task_id, task_data in running_tasks_by_ip[ip].items():
                if task_data.get('rag_system'):
                    task_data['rag_system'].stop_current_task()
            del running_tasks_by_ip[ip]
            print(f"已清理IP {ip} 的所有任務")

@app.route('/')
def index():
    # 清理過期任務
    cleanup_expired_tasks()
    
    # 獲取客戶端IP
    client_ip = get_client_ip()
    
    # 清理該IP的所有正在執行的任務
    cleanup_ip_tasks(client_ip)
    
    return render_template('index.html')

@app.route('/manage')
def manage():
    # 清理過期任務
    cleanup_expired_tasks()
    
    # 獲取客戶端IP
    client_ip = get_client_ip()
    
    # 清理該IP的所有正在執行的任務
    cleanup_ip_tasks(client_ip)
    
    return render_template('manage.html')

@app.route('/api/query/stream')
def query_stream():
    """處理實時查詢的 SSE 端點"""
    question = request.args.get('question', '')
    date_range = request.args.get('date_range', '').strip()
    
    if not question:
        return jsonify({'error': '問題不能為空'}), 400
    
    # 獲取客戶端IP
    client_ip = get_client_ip()
    
    # 生成唯一的任務ID
    task_id = str(uuid.uuid4())
    
    # 創建新的RAG系統實例
    task_rag_system = CustomRAGAgentSystem(reset_db=False, db_path="./custom_json_rag_db")
    
    # 記錄任務到對應的IP
    with task_lock:
        if client_ip not in running_tasks_by_ip:
            running_tasks_by_ip[client_ip] = {}
        running_tasks_by_ip[client_ip][task_id] = {
            'rag_system': task_rag_system,
            'start_time': time.time()
        }
    
    def generate():
        try:
            print(f"收到查詢請求: IP={client_ip}, 問題='{question}', 時間區間='{date_range}'")
            
            # 首先發送任務ID
            yield format_sse(json.dumps({
                'step': 'task_id',
                'task_id': task_id
            }))
            
            # 1. 搜索文檔步驟
            documents = task_rag_system.search_documents(question, n_results=4, date_range=date_range if date_range else None)
            print(f"搜索到 {len(documents)} 個文檔")
            
            if not documents:
                yield format_sse(json.dumps({
                    'step': 'error',
                    'message': '在指定時間範圍內沒有找到相關文檔'
                }))
                return
            
            search_results = [
                {
                    'filename': os.path.basename(doc['metadata']['source']),
                    'original_filename': doc['metadata'].get('original_filename', os.path.basename(doc['metadata']['source'])),
                    'similarity': 1 - doc['distance'],
                    'chunk_id': doc['metadata'].get('chunk_id', 0),
                    'timestamp': doc.get('timestamp', '')
                } for doc in documents
            ]
            
            # 發送搜索結果
            yield format_sse(json.dumps({
                'step': 'search',
                'results': search_results
            }))
            
            # 2. 篩選文檔步驟
            relevant_docs = []
            all_filter_interactions = {}  # 保存所有文檔的交互訊息
            
            for i, doc in enumerate(documents):
                # 發送當前正在處理的文檔信息
                yield format_sse(json.dumps({
                    'step': 'filter_progress',
                    'current_doc': {
                        'filename': os.path.basename(doc['metadata']['source']),
                        'original_filename': doc['metadata'].get('original_filename', os.path.basename(doc['metadata']['source'])),
                        'progress': f"正在分析第 {i+1}/{len(documents)} 個文檔",
                        'similarity': 1 - doc['distance'],
                        'status': 'analyzing'
                    }
                }))
                
                # 發送 filter_user_proxy 的思考過程
                yield format_sse(json.dumps({
                    'step': 'filter_thought',
                    'thought': f"正在評估文檔 '{doc['metadata'].get('original_filename', os.path.basename(doc['metadata']['source']))}' 與問題的相關性..."
                }))
                
                # 檢查文檔相關性
                relevant_docs_batch, filter_interactions = task_rag_system.filter_documents(question, [doc])
                
                # 保存交互訊息
                all_filter_interactions.update(filter_interactions)
                
                # 發送篩選結果
                doc_key = f"{doc['metadata'].get('original_filename', os.path.basename(doc['metadata']['source']))}_{doc['metadata'].get('chunk_id', 0)}"
                is_relevant = filter_interactions.get(doc_key, {}).get('is_relevant', False)
                
                yield format_sse(json.dumps({
                    'step': 'filter_result',
                    'result': {
                        'filename': doc['metadata'].get('original_filename', os.path.basename(doc['metadata']['source'])),
                        'is_relevant': is_relevant,
                        'thought': "這個文檔" + ("與問題高度相關" if is_relevant else "與問題關聯度較低")
                    }
                }))
                
                if is_relevant:
                    relevant_docs.append(doc)
            
            print(f"篩選後剩餘 {len(relevant_docs)} 個文檔")
            
            # 保存交互訊息到任務中，供後續API調用
            with task_lock:
                if client_ip in running_tasks_by_ip and task_id in running_tasks_by_ip[client_ip]:
                    running_tasks_by_ip[client_ip][task_id]['filter_interactions'] = all_filter_interactions
            
            if not relevant_docs:
                # 發送篩選結果（空結果）
                yield format_sse(json.dumps({
                    'step': 'filter',
                    'results': []
                }))
                
                # 直接進入答案步驟，返回沒有找到相關文檔的訊息
                yield format_sse(json.dumps({
                    'step': 'answer',
                    'answer': '沒有找到相關文檔來回答您的問題。'
                }))
                return
            
            filtered_results = [
                {
                    'filename': os.path.basename(doc['metadata']['source']),
                    'original_filename': doc['metadata'].get('original_filename', os.path.basename(doc['metadata']['source'])),
                    'relevance_score': doc.get('relevance_score', 1.0),
                    'chunk_id': doc['metadata'].get('chunk_id', 0),
                    'timestamp': doc.get('timestamp', '')
                } for doc in relevant_docs
            ]
            
            # 發送篩選結果
            yield format_sse(json.dumps({
                'step': 'filter',
                'results': filtered_results
            }))
            
            # 3. 生成答案步驟
            answer = task_rag_system.generate_answer(question, relevant_docs)
            
            # 發送最終答案
            yield format_sse(json.dumps({
                'step': 'answer',
                'answer': answer
            }))
            
            steps_data = {'search': None, 'filter': None, 'answer': None}
            steps_data['search'] = search_results
            steps_data['filter'] = filtered_results
            steps_data['answer'] = answer
            
            # 儲存歷史紀錄
            try:
                history_id = f"{int(time.time())}_{uuid.uuid4().hex}"
                history_obj = {
                    'id': history_id,
                    'timestamp': int(time.time()),
                    'question': question,
                    'date_range': date_range,
                    'steps': steps_data,
                    'task_id': task_id,
                    'filter_interactions': all_filter_interactions
                }
                os.makedirs(HISTORY_DIR, exist_ok=True)
                with open(os.path.join(HISTORY_DIR, f"{history_id}.json"), 'w', encoding='utf-8') as fp:
                    json.dump(history_obj, fp, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"儲存歷史紀錄失敗: {e}")
            
        except Exception as e:
            print(f"處理查詢時發生錯誤: {str(e)}")
            yield format_sse(json.dumps({
                'step': 'error',
                'message': f'處理查詢時發生錯誤: {str(e)}'
            }))
        finally:
            # 保存篩選交互訊息到已完成任務中
            with task_lock:
                if client_ip in running_tasks_by_ip and task_id in running_tasks_by_ip[client_ip]:
                    task_data = running_tasks_by_ip[client_ip][task_id]
                    if 'filter_interactions' in task_data:
                        with completed_task_lock:
                            completed_task_interactions[task_id] = {
                                'filter_interactions': task_data['filter_interactions'],
                                'completed_time': time.time()
                            }
                    del running_tasks_by_ip[client_ip][task_id]
                    
                    # 如果該IP沒有其他任務了，清理IP條目
                    if not running_tasks_by_ip[client_ip]:
                        del running_tasks_by_ip[client_ip]
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/query', methods=['POST'])
def query():
    data = request.get_json()
    question = data.get('question', '')
    
    if not question:
        return jsonify({'error': '問題不能為空'}), 400
    
    try:
        # 獲取RAG系統的處理過程
        documents = rag_system.search_documents(question, n_results=4)
        relevant_docs = rag_system.filter_documents(question, documents)
        answer = rag_system.generate_answer(question, relevant_docs)
        
        # 準備返回的數據
        result = {
            'answer': answer,
            'process': {
                'search_results': [
                    {
                        'filename': os.path.basename(doc['metadata']['source']),
                        'file_type': doc['metadata'].get('file_type', 'unknown'),
                        'similarity': 1 - doc['distance']
                    } for doc in documents
                ],
                'filtered_results': [
                    {
                        'filename': os.path.basename(doc['metadata']['source']),
                        'file_type': doc['metadata'].get('file_type', 'unknown')
                    } for doc in relevant_docs
                ]
            }
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def convert_doc_to_docx(doc_path):
    """將 .doc 文件轉換為 .docx 格式"""
    try:
        # 創建臨時文件
        temp_dir = tempfile.mkdtemp()
        docx_path = os.path.join(temp_dir, os.path.basename(doc_path) + 'x')
        
        # 使用 LibreOffice 進行轉換
        cmd = ['soffice', '--headless', '--convert-to', 'docx', '--outdir', temp_dir, doc_path]
        subprocess.run(cmd, check=True, capture_output=True)
        
        # 獲取轉換後的文件路徑
        converted_file = os.path.join(temp_dir, os.path.basename(doc_path) + 'x')
        if os.path.exists(converted_file):
            return converted_file
        return None
    except Exception as e:
        print(f"轉換 .doc 到 .docx 失敗: {str(e)}")
        return None

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '沒有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '沒有選擇文件'}), 400
    
    if file and allowed_file(file.filename):
        try:
            # 使用原始文件名作為 original_filename
            original_filename = file.filename
            # 使用安全的文件名作為存儲文件名
            safe_filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{safe_filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            # 確保上傳目錄存在
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # 保存文件
            file.save(filepath)
            
            try:
                file_ext = original_filename.rsplit('.', 1)[1].lower()
                
                # 只對文本文件進行 UTF-8 編碼驗證
                if file_ext in ['txt', 'md', 'json']:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if not content.strip():
                            raise ValueError("文件內容為空")
                
                success = False
                converted_file = None
                
                if file_ext == 'doc':
                    # 轉換 .doc 到 .docx
                    converted_file = convert_doc_to_docx(filepath)
                    if converted_file:
                        success = rag_system.add_word_document(converted_file, original_filename=original_filename)
                    else:
                        raise Exception("無法轉換 .doc 文件到 .docx 格式")
                elif file_ext == 'docx':
                    success = rag_system.add_word_document(filepath, original_filename=original_filename)
                elif file_ext in ['xlsx', 'xls']:
                    success = rag_system.add_excel_document(filepath, original_filename=original_filename)
                elif file_ext == 'json':
                    success = rag_system.add_json_document(filepath, original_filename=original_filename)
                elif file_ext == 'pdf':
                    success = rag_system.add_document(filepath, doc_type="pdf", original_filename=original_filename)
                else:
                    success = rag_system.add_document(filepath, doc_type="txt", original_filename=original_filename)
                
                if success:
                    return jsonify({
                        'message': '文件上傳成功',
                        'original_filename': original_filename,
                        'stored_path': filepath
                    })
                else:
                    raise Exception("文件處理失敗")
                    
            except Exception as e:
                print(f"處理文件時發生錯誤: {str(e)}")
                return jsonify({'error': f'文件處理失敗: {str(e)}'}), 500
            finally:
                # 清理臨時文件
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except Exception as e:
                        print(f"清理臨時文件失敗: {str(e)}")
                if converted_file and os.path.exists(converted_file):
                    try:
                        os.remove(converted_file)
                        os.rmdir(os.path.dirname(converted_file))
                    except Exception as e:
                        print(f"清理轉換後的文件失敗: {str(e)}")
        
        except Exception as e:
            print(f"上傳文件時發生錯誤: {str(e)}")
            return jsonify({'error': f'上傳文件失敗: {str(e)}'}), 500
    
    return jsonify({'error': '不支持的文件類型'}), 400

@app.route('/api/documents', methods=['GET'])
def list_documents():
    try:
        all_docs = rag_system.collection.get(include=["metadatas"])
        file_stats = {}
        
        for metadata in all_docs["metadatas"]:
            source = metadata.get("source", "unknown")
            display_name = metadata.get("original_filename", os.path.basename(source))
            file_type = metadata.get("file_type", "unknown")
            
            if source not in file_stats:
                file_stats[source] = {
                    "chunks": 0,
                    "type": file_type,
                    "path": source,
                    "display_name": display_name,
                    "original_filename": metadata.get("original_filename"),
                    "extra_info": {}
                }
            file_stats[source]["chunks"] += 1
            
            if file_type == "docx":
                file_stats[source]["extra_info"]["paragraphs"] = metadata.get("paragraphs_count", 0)
                file_stats[source]["extra_info"]["tables"] = metadata.get("tables_count", 0)
            elif file_type == "excel":
                file_stats[source]["extra_info"]["sheets"] = metadata.get("sheets_count", 0)
                file_stats[source]["extra_info"]["sheet_names"] = metadata.get("sheet_names", [])
        
        return jsonify(list(file_stats.values()))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<path:filename>', methods=['DELETE'])
def delete_document(filename):
    try:
        all_docs = rag_system.collection.get(include=["ids", "metadatas"])
        doc_ids_to_delete = []
        
        # 遍歷所有文檔，找到匹配的文件
        for i, metadata in enumerate(all_docs["metadatas"]):
            source = metadata.get("source", "")
            original_filename = metadata.get("original_filename", "")
            
            # 檢查是否匹配原始文件名或源文件路徑
            # 使用 basename 來比較文件名，避免路徑差異
            if (os.path.basename(source) == os.path.basename(filename) or 
                original_filename == filename or 
                os.path.basename(source) == filename):
                doc_ids_to_delete.append(all_docs["ids"][i])
        
        if doc_ids_to_delete:
            # 刪除文檔
            rag_system.collection.delete(ids=doc_ids_to_delete)
            return jsonify({'message': '文檔刪除成功'})
        else:
            return jsonify({'error': '找不到指定的文檔'}), 404
            
    except Exception as e:
        print(f"刪除文檔時發生錯誤: {str(e)}")
        return jsonify({'error': f'刪除文檔失敗: {str(e)}'}), 500

@app.route('/api/documents/batch', methods=['DELETE'])
def batch_delete_documents():
    try:
        data = request.get_json()
        filenames = data.get('filenames', [])
        
        if not filenames:
            return jsonify({'error': '未指定要刪除的文件'}), 400
            
        all_docs = rag_system.collection.get(include=["ids", "metadatas"])
        doc_ids_to_delete = []
        
        # 遍歷所有文檔，找到匹配的文件
        for i, metadata in enumerate(all_docs["metadatas"]):
            source = metadata.get("source", "")
            original_filename = metadata.get("original_filename", "")
            
            # 檢查是否匹配任何要刪除的文件名
            for filename in filenames:
                if (os.path.basename(source) == os.path.basename(filename) or 
                    original_filename == filename or 
                    os.path.basename(source) == filename):
                    doc_ids_to_delete.append(all_docs["ids"][i])
                    break
        
        if doc_ids_to_delete:
            # 批量刪除文檔
            rag_system.collection.delete(ids=doc_ids_to_delete)
            return jsonify({
                'message': f'成功刪除 {len(doc_ids_to_delete)} 個文檔',
                'deleted_count': len(doc_ids_to_delete)
            })
        else:
            return jsonify({'error': '找不到指定的文檔'}), 404
            
    except Exception as e:
        print(f"批量刪除文檔時發生錯誤: {str(e)}")
        return jsonify({'error': f'批量刪除文檔失敗: {str(e)}'}), 500

@app.route('/api/document_content/<path:original_filename>', methods=['GET'])
def get_document_content(original_filename):
    try:
        chunk_id = request.args.get('chunk_id')
        if chunk_id is not None:
            try:
                chunk_id = int(chunk_id)
            except ValueError:
                return jsonify({'error': '無效的段落ID'}), 400
            
        all_docs = rag_system.collection.get(include=["ids", "documents", "metadatas"])
        document_chunks = []
        
        # 收集所有匹配的文檔片段
        for i, metadata in enumerate(all_docs["metadatas"]):
            if metadata.get("original_filename") == original_filename:
                # 如果指定了 chunk_id，只返回該段落
                if chunk_id is not None and metadata.get("chunk_id") != chunk_id:
                    continue
                    
                document_chunks.append({
                    'content': all_docs["documents"][i],
                    'file_type': metadata.get("file_type", "unknown"),
                    'chunk_id': metadata.get("chunk_id", 0),
                    'metadata': metadata
                })
        
        if document_chunks:
            # 按 chunk_id 排序
            document_chunks.sort(key=lambda x: x['chunk_id'])
            
            # 如果指定了 chunk_id，只返回該段落的內容
            if chunk_id is not None:
                if not document_chunks:
                    return jsonify({'error': f'找不到段落 {chunk_id}'}), 404
                return jsonify({
                    'content': document_chunks[0]['content'],
                    'file_type': document_chunks[0]['file_type'],
                    'chunk_id': document_chunks[0]['chunk_id']
                })
            
            # 否則返回所有段落
            return jsonify({
                'content': "\n\n--- 段落分隔線 ---\n\n".join(
                    f"段落 {chunk['chunk_id']}:\n{chunk['content']}" 
                    for chunk in document_chunks
                ),
                'file_type': document_chunks[0]['file_type'],
                'total_chunks': len(document_chunks),
                'chunks': document_chunks
            })
        
        return jsonify({'error': '找不到指定的文檔'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/filter_interaction/<path:filename>', methods=['GET'])
def get_filter_interaction(filename):
    """獲取文檔篩選的交互訊息"""
    try:
        chunk_id = request.args.get('chunk_id')
        task_id = request.args.get('task_id')
        if not task_id:
            return jsonify({'error': '缺少任務ID'}), 400
        if chunk_id is not None:
            try:
                chunk_id = int(chunk_id)
            except ValueError:
                return jsonify({'error': '無效的段落ID'}), 400
        # 首先從正在執行的任務中獲取交互訊息
        filter_interactions = None
        with task_lock:
            # 在所有IP的任務中查找指定的task_id
            for ip, tasks in running_tasks_by_ip.items():
                if task_id in tasks:
                    task_data = tasks[task_id]
                    filter_interactions = task_data.get('filter_interactions', {})
                    break
        # 如果不在運行中的任務，檢查已完成的任務
        if filter_interactions is None:
            with completed_task_lock:
                if task_id in completed_task_interactions:
                    filter_interactions = completed_task_interactions[task_id]['filter_interactions']
        # 如果還是沒有，從歷史紀錄檔案讀取
        if filter_interactions is None:
            # 在 history 目錄下尋找對應 task_id 的 json 檔案
            for f in glob.glob(os.path.join(HISTORY_DIR, '*.json')):
                try:
                    with open(f, 'r', encoding='utf-8') as fp:
                        data = json.load(fp)
                        if data.get('task_id') == task_id and 'filter_interactions' in data:
                            filter_interactions = data['filter_interactions']
                            break
                except Exception:
                    continue
            if filter_interactions is None:
                return jsonify({'error': '任務不存在或已過期'}), 404
        # 構建文檔鍵
        if chunk_id is not None:
            doc_key = f"{filename}_{chunk_id}"
        else:
            doc_key = None
            for key in filter_interactions.keys():
                if key.startswith(f"{filename}_"):
                    doc_key = key
                    break
        if doc_key and doc_key in filter_interactions:
            interaction_data = filter_interactions[doc_key]
            return jsonify({
                'filename': interaction_data['filename'],
                'chunk_id': interaction_data['chunk_id'],
                'is_relevant': interaction_data['is_relevant'],
                'messages': interaction_data['messages'],
                'error': interaction_data.get('error')
            })
        else:
            return jsonify({'error': '找不到指定的文檔交互訊息'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/history')
def history():
    cleanup_expired_tasks()
    client_ip = get_client_ip()
    cleanup_ip_tasks(client_ip)
    return render_template('history.html')

@app.route('/api/history/list', methods=['GET'])
def history_list():
    try:
        history_files = sorted(glob.glob(os.path.join(HISTORY_DIR, '*.json')), reverse=True)
        history_list = []
        for f in history_files:
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                    history_list.append({
                        'id': data.get('id', os.path.basename(f)),
                        'timestamp': data.get('timestamp'),
                        'question': data.get('question'),
                        'date_range': data.get('date_range'),
                        'answer': data.get('steps', {}).get('answer', ''),
                        'filename': os.path.basename(f),
                        'task_id': data.get('task_id', None)
                    })
            except Exception as e:
                continue
        return jsonify(history_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/<history_id>', methods=['GET'])
def history_detail(history_id):
    try:
        file_path = os.path.join(HISTORY_DIR, history_id)
        if not file_path.endswith('.json'):
            file_path += '.json'
        if not os.path.exists(file_path):
            return jsonify({'error': '找不到歷史紀錄'}), 404
        with open(file_path, 'r', encoding='utf-8') as fp:
            data = json.load(fp)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/history/<history_id>')
def history_detail_page(history_id):
    return render_template('history_detail.html', history_id=history_id)

@app.route('/api/history/<history_id>', methods=['DELETE'])
def delete_history(history_id):
    try:
        file_path = os.path.join(HISTORY_DIR, history_id)
        if not file_path.endswith('.json'):
            file_path += '.json'
        if not os.path.exists(file_path):
            return jsonify({'error': '找不到歷史紀錄'}), 404
        os.remove(file_path)
        return jsonify({'message': '歷史紀錄刪除成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/batch', methods=['DELETE'])
def batch_delete_history():
    try:
        data = request.get_json()
        filenames = data.get('filenames', [])
        if not filenames:
            return jsonify({'error': '未指定要刪除的歷史紀錄'}), 400
        deleted = 0
        for filename in filenames:
            file_path = os.path.join(HISTORY_DIR, filename)
            if not file_path.endswith('.json'):
                file_path += '.json'
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted += 1
        return jsonify({'message': f'成功刪除 {deleted} 筆歷史紀錄', 'deleted_count': deleted})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 設置 host='0.0.0.0' 使其監聽所有網絡接口
    # port=5000 是默認端口，可以根據需要修改
    HISTORY_DIR = 'history'
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True) 