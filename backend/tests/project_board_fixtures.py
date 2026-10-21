"""Entirely invented acceptance scenarios. Never read the sensitive HTML or a real ledger."""
from project_data import FIELDS


def synthetic_projects():
    scenarios = [
        {"name": "虚构验收一：单业务光伏", "pvArea": "1500", "pvCapacity": "0.589"},
        {"name": "虚构验收二：光伏与储能", "pvArea": "2400㎡", "pvCapacity": "7.92E-2", "storageCapacity": "0.12"},
        {"name": "虚构验收三：充电桩长配置", "chargingScale": "虚构配置：两套直流设备及配套交流终端，站点布置和接入条件仍需核查。" * 8},
        {"name": "虚构验收四：能源节能方案", "energyType": "虚构综合节能", "energyScale": "虚构测算：节能率约18%，年节约电费约12万元。保留完整方案，不代表实际收益。" * 6},
        {"name": "虚构验收五：不连续节点", "pvCapacity": "0.06699999999999999", "stages": ["已完成", None, "待核实", None, None, None, "进行中", None, None, None, None], "currentStage": "合同签约"},
        {"name": "虚构验收六：明确更新", "storageCapacity": "尚不能确定", "progressUpdate": "有"},
        {"name": "虚构验收七：待协调事项", "chargingScale": "4台", "coordination": "虚构事项：请协调跨部门接口人与方案确认。"},
        {"name": "虚构验收八：长项目名称与长实施情况·" + "仅用于排版验收的合成文字" * 8, "pvCapacity": "0.18MW", "energyType": "虚构余热利用", "energyScale": "原始说明待完善", "situation": "虚构实施情况：资料校验与方案讨论仍在进行，后续须确认场地条件。\n" * 40},
    ]
    result = []
    for index, changes in enumerate(scenarios, 1):
        project = dict.fromkeys(FIELDS)
        project.update(serial=str(index), leader=f"虚构组长{(index % 2) + 1}", owner=f"虚构负责人{(index % 3) + 1}",
                       resource=f"完全虚构资源{index}", management="虚构管理关系", ownership="虚构所有权",
                       priority="甲：尽快推进" if index % 2 else "乙：持续跟进", valueRating="虚构评级",
                       customerType="虚构客户", district=f"虚构片区{(index % 2) + 1}",
                       stages=["已完成", "进行中"] + [None] * 9, currentStage="实地勘察",
                       situation="虚构最新情况：正在开展初步沟通。", nextStep="虚构下一步：核对资料并安排讨论。",
                       coordination=None, progressUpdate="无")
        project.update(changes)
        result.append(project)
    return result
