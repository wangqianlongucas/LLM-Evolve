"""日志保存模块"""
import json
import os
from datetime import datetime

class ExperimentLogger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.exp_dir = os.path.join(log_dir, f"exp_{self.timestamp}")
        
        # 创建日志目录
        os.makedirs(self.exp_dir, exist_ok=True)
        
        # 初始化日志数据
        self.logs = {
            "start_time": self.timestamp,
            "generations": [],
            "best_history": []
        }
        
        # 初始化追加文件
        self.operators_log = os.path.join(self.exp_dir, "all_operators.txt")
        self.prompts_log = os.path.join(self.exp_dir, "all_prompts.txt")
        
        print(f"📁 日志目录: {self.exp_dir}")
    
    def log_generation(self, gen, data):
        """记录每代信息"""
        self.logs["generations"].append({
            "generation": gen,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            **data
        })
        
        # 实时保存
        self._save_json()
    
    def log_best(self, best_individual):
        """记录最优个体"""
        self.logs["best_history"].append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "id": best_individual["id"],
            "fitness": best_individual["fitness"],
            "time": best_individual.get("time", 0)
        })
    
    def save_best_operator(self, best_individual):
        """保存最优算子代码"""
        best_file = os.path.join(self.exp_dir, "best_operator.py")
        with open(best_file, 'w', encoding='utf-8') as f:
            f.write(f"# Best Operator\n")
            f.write(f"# ID: {best_individual['id']}\n")
            f.write(f"# Fitness: {best_individual['fitness']:.2f}\n")
            f.write(f"# Time: {best_individual.get('time', 0):.2f}s\n")
            f.write(f"# Parent: {best_individual.get('parent_id', 'N/A')}\n")
            f.write(f"# Prompt: {best_individual.get('prompt_used', 'N/A')}\n\n")
            f.write(best_individual['code'])
        print(f"💾 最优算子已保存: {best_file}")
    
    def save_population(self, gen, operator_pop, prompt_pop):
        """保存当前种群的所有算子代码（追加模式）"""
        # 追加算子代码到统一文件
        with open(self.operators_log, 'a', encoding='utf-8') as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"第 {gen} 代算子种群 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
            f.write("=" * 80 + "\n\n")
            
            # 按fitness排序
            sorted_ops = sorted(operator_pop, key=lambda x: x["fitness"])
            
            for i, ind in enumerate(sorted_ops):
                f.write(f"{'='*80}\n")
                f.write(f"算子 #{i+1}\n")
                f.write(f"{'='*80}\n")
                f.write(f"ID: {ind['id']}\n")
                f.write(f"Fitness: {ind['fitness']:.2f}\n")
                f.write(f"Time: {ind.get('time', 0):.2f}s\n")
                f.write(f"Parent: {ind.get('parent_id', 'N/A')}\n")
                f.write(f"Prompt: {ind.get('prompt_used', 'N/A')}\n")
                f.write(f"Source: {ind.get('source', 'N/A')}\n")
                f.write(f"\n代码:\n")
                f.write("-" * 80 + "\n")
                f.write(ind["code"])
                f.write("\n" + "-" * 80 + "\n\n")
        
        # 追加Prompt种群到统一文件
        with open(self.prompts_log, 'a', encoding='utf-8') as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"第 {gen} 代Prompt种群 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
            f.write("=" * 80 + "\n\n")
            
            # 按fitness排序
            sorted_prompts = sorted(prompt_pop, key=lambda x: x["fitness"], reverse=True)
            
            for i, p in enumerate(sorted_prompts):
                f.write(f"{i+1}. {p['text']}\n")
                f.write(f"   Fitness: {p['fitness']:.3f}, 使用次数: {p['usage_count']}\n\n")
    
    def _save_json(self):
        """保存主日志文件"""
        log_file = os.path.join(self.exp_dir, "experiment_log.json")
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, indent=2, ensure_ascii=False)
    
    def save_summary(self, best_individual, config):
        """保存实验总结"""
        summary_file = os.path.join(self.exp_dir, "summary.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("实验总结\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"开始时间: {self.logs['start_time']}\n")
            f.write(f"结束时间: {datetime.now().strftime('%Y%m%d_%H%M%S')}\n\n")
            
            f.write("配置参数:\n")
            for key, value in config.items():
                f.write(f"  {key}: {value}\n")
            f.write("\n")
            
            f.write("最优结果:\n")
            f.write(f"  ID: {best_individual['id']}\n")
            f.write(f"  Fitness: {best_individual['fitness']:.2f}\n")
            f.write(f"  Time: {best_individual.get('time', 0):.2f}s\n")
            f.write(f"  Parent: {best_individual.get('parent_id', 'N/A')}\n")
            f.write(f"  Prompt: {best_individual.get('prompt_used', 'N/A')}\n\n")
            
            f.write("进化历史:\n")
            for entry in self.logs["best_history"]:
                f.write(f"  [{entry['timestamp']}] {entry['id']}: {entry['fitness']:.2f}\n")
        
        print(f"📄 实验总结已保存: {summary_file}")

