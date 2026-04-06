"""CVRP主入口"""
import json
from cvrp_problem import CVRPInstance
from cvrp_ea_main import CVRPEAController

def load_instances(filepath, limit=None):
    """加载CVRP算例"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    instances = []
    for item in data[:limit] if limit else data:
        instances.append(CVRPInstance(
            name=item["name"],
            coords=item["coords"],
            demands=item["demands"],
            capacity=item["capacity"],
            num_vehicles=item.get("num_vehicles"),
            optimal=item.get("optimal")
        ))
    return instances

def main():
    # 加载算例（先用2个测试）
    print("📂 加载CVRP算例...")
    instances = load_instances("data/cvrp_instances.json", limit=2)
    
    for inst in instances:
        print(f"  - {inst.name}: {inst.n_customers}个客户, 容量={inst.capacity}, "
              f"车辆数={inst.num_vehicles}, 最优解={inst.optimal}")
    print()
    
    # 运行EA
    controller = CVRPEAController(instances)
    best_operator = controller.run()
    
    print(f"\n{'='*60}")
    print("🏆 最终结果")
    print(f"{'='*60}")
    print(f"最优算子ID: {best_operator['id']}")
    print(f"Fitness: {best_operator['fitness']:.2f}")
    print(f"来源: {best_operator.get('source', 'evolved')}")
    print(f"\n代码:\n{best_operator['code']}")

if __name__ == "__main__":
    main()
