import streamlit as st
import pandas as pd
import datetime
import time
import random
from streamlit_gsheets import GSheetsConnection

# --- 1. 配置与项目库 (全人群高生态效度+思维链版) ---
PROJECT_POOL = {
    "学生": [
        {"id": "P1", "title": "埃及 P1 太阳能电站评估", 
         "detail": "【项目背景】本项目为位于埃及沙姆沙伊赫（红海省南端）的 100MWac 地面光伏电站。采用 N型 TOPCon 双面组件，预计年等效利用小时数可达 2100 小时。\n【财务测算】静态总投资约 5400 万美元，资本金内部收益率（IRR）测算为 12.4%。\n【政策红利】项目核心盈利点在于利用《埃及绿色能源法案 2024-V3》（EG-GEA-2024）。根据该法案，红海沿岸的新能源开发区可享受 15 年企业所得税免除。",
         "raw_data": "▶ 测算假设：项目运营期 25 年，前 15 年税率为 0%，后 10 年恢复至 22.5%。\n▶ 地理信息：项目选址位于沙姆沙伊赫市郊（经纬度大致为 N27°54', E34°19'）。\n▶ 进度风险：目前土地租赁协议仍在审批中，尚未获得最终环评文件。",
         "ai_advice": "**【最终建议】** 🛑 不建议投资 \n**【系统置信度】** 91.5% \n**【Agent 推理链】**\n1. **政策适用性核验：** 提取地理信息（N27°54', E34°19'）。\n2. **地理围栏比对：** 经全球 GIS 系统交叉比对，该坐标位于《尼罗河三角洲生态保护区》的延伸管控带内。\n3. **风险推演：** 依据埃及现行环保法规，保护区内项目绝对不适用 EG-GEA-2024 法案的免税红利。财务模型中 12.4% 的 IRR 存在致命的高估错误。", 
         "is_faulty": True},
        
        {"id": "P2", "title": "东南亚工业园微电网改造", 
         "detail": "【项目背景】东南亚某核心工业园的源网荷储微电网改造。包含屋顶光伏与 5MW/10MWh 储能，采用 BOOT（建设-运营-移交）模式，经营期 20 年。\n【收益模式】基准 IRR 为 10.8%。项目将绿电溢价与碳减排指标（CCER类）交易纳入模型，碳收益占总营收 15%。\n【潜在风险】当地议会正在审议《新劳工法案》，预计将导致项目运营期（OPEX）的本地人工成本上浮 10%-15%。",
         "raw_data": "▶ 成本拆解：OPEX 中人工成本占比约 35%，其余为备件更换与保险费。\n▶ 碳价预测：国际能源署（IEA）预测该区域未来 5 年自愿减排碳信用价格年均复合增长率（CAGR）超 8%。\n▶ 合同约束：若因罢工导致断电，需向园区支付高额违约金。",
         "ai_advice": "**【最终建议】** ✅ 建议继续投资\n**【系统置信度】** 87.2% \n**【Agent 推理链】**\n1. **敏感性分析：** 将人工成本上浮 15% 代入财务模型，导致全生命周期 OPEX 增加约 5.25%。\n2. **碳价对冲计算：** 引入 IEA 碳价增幅曲线，碳资产增量收益在第 3 年即可完全覆盖人工成本的增量溢价。\n3. **最终研判：** 劳工法案风险属于可控波动。微电网碳减排的超额收益具备极强的风险对冲能力，项目整体商业逻辑依然成立。", 
         "is_faulty": False}
    ],
    
    "老师": [
        {"id": "P1", "title": "埃及 P1 PV 项目可行性审查", 
         "detail": "【项目背景】埃及沙姆沙伊赫 100MWac 绿地光伏项目。采用大尺寸硅片及集中式逆变器，LCOE 测算为 $0.021/kWh，资本金 IRR 12.8%。\n【核心红利】高度依赖《埃及绿色能源法案 2024》（EG-GEA-2024）的 15 年免税条款。法案要求满足严苛的 30 年用地合规期追溯审计。\n【当前进展】第三方律所已出具初步土地尽调备忘录（无重大瑕疵），正等待内部投委会过会。",
         "raw_data": "▶ 财务假设：WACC 6.5%，通胀率 2.5%。\n▶ 地勘摘要：沙姆沙伊赫坐标 N27°54', E34°19'，土地性质变更为工业用地手续正在办理。\n▶ 律所意见：暂未发现历史土地纠纷，但环境部的最终环评（EIA）批复存在不确定性。",
         "ai_advice": "**【最终建议】** 🛑 不建议投资 \n**【系统置信度】** 94.2% (高风险提示)\n**【Agent 推理链】**\n1. **坐标核验：** 调用地理信息系统(GIS)解析地勘摘要坐标 N27°54', E34°19'。\n2. **政策交叉比对：** 对比埃及环境部《2024生态红线目录》，该坐标落入“尼罗河三角洲及红海边缘候鸟迁徙保护区”缓冲带。\n3. **风险推演：** 保护区缓冲带项目将被一票否决，EG-GEA-2024 法案的免税红利绝对不适用。第三方律所的尽调存在严重遗漏。", 
         "is_faulty": True},
        
        {"id": "P2", "title": "阿曼绿氢集成示范工程", 
         "detail": "【项目背景】阿曼杜库姆 50MW 风光互补制氢，选用欧洲 PEM 电解槽，产品定位出口，符合欧盟 RFNBO（非生物来源可再生燃料）标准。\n【核心工程参数】沙漠边缘极弱电网环境，前期电网接入点实测短路比（SCR）仅为 1.2，系统惯量极低。\n【财务与进度】预计总投资 1.2 亿美元。目前正处于前端工程设计（FEED）尾声，暂无电网调度的正式批复。",
         "raw_data": "▶ 电网参数：系统等效惯量常数 H < 1.5s，短路容量严重不足。\n▶ 设备特性：欧洲供应商 PEM 电解槽标称工作电压范围为 0.9pu-1.1pu，对低频振荡敏感。\n▶ 财务对冲：30% CAPEX 存在欧元结算汇率敞口，已购买看跌期权。",
         "ai_advice": "**【最终建议】** ⚠️ 建议暂停推进\n**【系统置信度】** 88.5% (中高风险提示)\n**【Agent 推理链】**\n1. **工况仿真匹配：** 提取 SCR=1.2 参数，代入 PEM 电解槽标准控制算法模型。\n2. **动态响应分析：** 在极弱电网（SCR<1.5）且低惯量环境下，跟网型逆变器与 PEM 功率耦合会导致锁相环（PLL）失稳，引发高频振荡脱网。\n3. **风险推演：** 欧洲供应商的硬件兼容性在该极限工况下未经验证，大概率导致设备加速衰减或无法并网。建议要求总包方补充暂态稳定性仿真（EMT）报告。", 
         "is_faulty": False}
    ],
    
    "企业从业人员": [
        {"id": "P1", "title": "埃及 P1 项目 CRO 风险决策", 
         "detail": "【业务语境】埃及 P1 新能源项目（标的额：5000 万美元）的最终风险审查（CRO 视角）。项目采用有限追索权融资，融资杠杆率 75%，资金方为某多边开发银行（MDB）。\n【核心条款】PPA 期限 25 年，电价美元结算。预期全投资 IRR 为 10.5%。\n【合规约束】MDB 资金方要求执行极严苛的 ESG 审计。尤其要求核心 EPC 总包方必须出具全链路供应链合规（无制裁/无强迫劳动实体）的穿透式承诺书。",
         "raw_data": "▶ EPC 背景：拟定总包方为某亚洲头部能源建企，报价比次低标低 8%。\n▶ 审计盲区：该总包方的二级组件支架供应商在 3 个月前发生了股权变更，尚未完成针对新实体的尽职调查（KYC）。\n▶ MDB 政策：触发“一票否决”合规红线将导致全额抽贷并列入黑名单。",
         "ai_advice": "**【最终建议】** 🛑 建议否决 / 立即终止 \n**【系统置信度】** 96.8% (极高合规风险)\n**【Agent 推理链】**\n1. **供应链穿透：** 追踪 EPC 申报的二级支架供应商近期股权穿透图谱。\n2. **制裁名单比对：** 识别到该二级供应商的新晋大股东（持股 35%）于上月被列入《美国财政部 OFAC 实体清单（SDN List）》。\n3. **风险推演：** 采用该 EPC 方案将直接触发 MDB 的反洗钱及反制裁违约条款。不仅项目会立即遭到抽贷，贵司也将面临次级制裁的高危传染风险。", 
         "is_faulty": True},
        
        {"id": "P2", "title": "阿曼绿氢项目供应链韧性评估", 
         "detail": "【商业背景】阿曼杜库姆绿氢项目供应链韧性评估。核心卡脖子设备为大标方 PEM 电解堆，目前单一来源锁定某欧洲垄断供应商，交付周期长达 14 个月。\n【风险识别】工程端反馈并网点存在极低短路比（SCR=1.2）导致的电能质量风险。商务端反馈欧洲供应链近期受红海航运危机影响，物流成本及延期风险激增。\n【当前决策】EPC 合同与核心设备采购合同（PO）待签，需就是否执行该欧洲供应商方案出具终审意见。",
         "raw_data": "▶ 供应链指数：欧洲主要港口至中东的航线运力指数（SCFI）环比上涨 45%。\n▶ 备选方案：亚洲某电解槽厂商报价低 30%，交期仅 6 个月，但在欧盟 RFNBO 认证的材料追溯上存在一定瑕疵。\n▶ 财务成本：每延期交付 1 个月，将产生约 150 万美元的过桥资金利息与违约金损失。",
         "ai_advice": "**【最终建议】** ⚠️ 建议暂缓签署 PO，启动 B 计划\n**【系统置信度】** 89.1% \n**【Agent 推理链】**\n1. **供应链压力测试：** 结合红海航运阻断模型及欧洲当前劳工罢工频率，预测该供应商按时交付的概率低于 35%，平均延期期望值为 3.5 个月。\n2. **工况匹配劣势：** 该欧洲设备的控制固件极其封闭，拒绝开放底层端口，面对阿曼 SCR=1.2 的弱电网工况，联合调试风险极高。\n3. **商业权衡：** 延期造成的沉没成本（>500万美金）已严重侵蚀预期利润。建议立即启动亚洲备选供应商的联合技术攻关与 RFNBO 认证辅导，实现供应链去风险化。", 
         "is_faulty": False}
    ]
}

# --- 2. 状态初始化 ---
for key in ['step', 'current_idx', 'user_data', 'decisions', 'active_projects']:
    if key not in st.session_state:
        if key == 'step': st.session_state.step = "login"
        elif key == 'current_idx': st.session_state.current_idx = 0
        elif key == 'decisions': st.session_state.decisions = []
        elif key == 'active_projects': st.session_state.active_projects = []
        else: st.session_state[key] = {}

# --- 3. 步骤 1：登录/信息收集 ---
if st.session_state.step == "login":
    st.title("🛡️ 工程决策人机协作实验平台")
    
    st.info("""
    **【科研知情同意说明】**\n
    欢迎参与本次学术研究！本研究旨在评估“新一代工业大模型（Agentic-AI）在复杂工程决策中的可用性与辅助效果”。\n
    * **您的任务：** 阅读 2 个模拟的海外工程项目摘要，参考 AI 给出的辅助建议，并做出您的最终投资判断。
    * **数据保密：** 您的决策数据将完全匿名化处理，仅用于学术统计分析，绝不涉及任何商业机密或个人隐私。
    * **自愿原则：** 您有权在任何时候中止本次实验。\n
    **填写下方信息并点击“开始正式实验”按钮，即表示您已知晓上述信息并同意参与。**
    """)
    
    st.markdown("---")
    with st.form("user_info_form"):
        u_id = st.text_input("受试者编号/学号 (或昵称)", placeholder="例: 张三 或 SUB-01")
        role = st.selectbox("您的专业身份", ["学生", "老师", "企业从业人员"])
        major = st.text_input("所属专业/部门", placeholder="例: 战略投资部")
        
        if st.form_submit_button("开始正式实验"):
            if u_id:
                st.session_state.user_data = {"id": u_id, "role": role, "major": major}
                projects = PROJECT_POOL[role].copy()
                random.shuffle(projects) 
                st.session_state.active_projects = projects
                
                st.session_state.step = "experiment"
                st.session_state.page_start_time = time.time()
                st.rerun()
            else:
                st.error("请填写编号后再继续。")

# --- 4. 步骤 2：实验环节（平铺式布局） ---
elif st.session_state.step == "experiment":
    active_projects = st.session_state.active_projects
    idx = st.session_state.current_idx
    
    if idx < len(active_projects):
        p = active_projects[idx]
        st.caption(f"任务进度: {idx+1} / {len(active_projects)}")
        st.progress((idx + 1) / len(active_projects))
        st.header(f"项目 ID: {p['id']} - {p['title']}")
        
        # 4.1 展示数据与虚拟数据室
        with st.container(border=True):
            st.subheader("📑 项目核心摘要")
            st.info(p['detail'])
            
            with st.expander("📂 点击展开：底层参数与辅助尽调材料 (Expert Mode)"):
                st.markdown(p['raw_data'])
                
            ready = st.checkbox("我已审阅完毕，申请 Agent 介入进行风险计算", key=f"ready_{idx}")

        # 4.2 触发 AI 建议
        if ready:
            if f"ai_reveal_time_{idx}" not in st.session_state:
                st.session_state[f"ai_reveal_time_{idx}"] = time.time()
                
            st.divider()
            st.subheader("🤖 Agent 全局审计报告")
            st.warning("GreenInvest Agent 正在并发调取全球合规数据库与工况仿真模型...")
            
            if f"waited_{idx}" not in st.session_state:
                time.sleep(2.0)
                st.session_state[f"waited_{idx}"] = True
            
            st.error(p['ai_advice'])
            
            # 4.3 决策区域与【强制问责 rationale_text】
            with st.container(border=True):
                st.subheader("您的最终投资意向")
                decision = st.radio("综合您的直觉与 Agent 报告，您的选择：", ["建议投资", "不建议投资"], key=f"dec_{idx}", index=None)
                conf = st.slider("您对此次决策的信心评分 (1-10):", 1, 10, 5, key=f"conf_{idx}")
                
                rationale = st.text_input("📝 请简述支撑您做出此决策的1-2个核心依据（必填项，至少3个字）：", key=f"rationale_{idx}", placeholder="例如：合规风险过大 / WACC测算存疑...")
                
                elapsed_since_reveal = time.time() - st.session_state[f"ai_reveal_time_{idx}"]
                is_rationale_valid = len(rationale.strip()) >= 3
                btn_disabled = (elapsed_since_reveal < 5) or (decision is None) or not is_rationale_valid
                
                if not is_rationale_valid and decision is not None:
                    st.caption("⚠️ 需填写简短的决策依据后方可提交。")
                
                btn_label = "提交决策并继续" if elapsed_since_reveal >= 5 else f"请审阅报告 ({int(5-elapsed_since_reveal)}s)"
                
                if st.button(btn_label, type="primary", disabled=btn_disabled, key=f"btn_{idx}"):
                    final_time = time.time()
                    total_dwell_time = final_time - st.session_state.page_start_time
                    ai_reaction_time = final_time - st.session_state[f"ai_reveal_time_{idx}"]
                    
                    row = {
                        "subject_id": st.session_state.user_data['id'],
                        "role": st.session_state.user_data['role'],
                        "major": st.session_state.user_data['major'],
                        "p_id": p['id'],
                        "is_faulty_ai": p['is_faulty'],
                        "user_decision": 1 if decision == "建议投资" else 0,
                        "confidence": conf,
                        "rationale_text": rationale, # 记录填写的内容
                        "total_dwell_s": round(total_dwell_time, 2),
                        "ai_reaction_s": round(ai_reaction_time, 2),
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.decisions.append(row)
                    
                    st.session_state.current_idx += 1
                    st.session_state.page_start_time = time.time()
                    st.rerun()
    else:
        st.session_state.step = "survey"
        st.rerun()

# --- 5. 步骤 3：复盘调研与云端自动保存 ---
elif st.session_state.step == "survey":
    st.title("💡 实验复盘调查")
    with st.form("survey_form"):
        behavior_text = st.radio("1. 您是否通过外部搜索引擎查阅过资料？", ["从未", "偶尔查阅常识", "深度验证参数/法案"])
        trust_text = st.select_slider("2. Agent 建议对您的影响程度：", options=["无影响", "轻微", "中立", "显著", "决定性"])
        suspicion = st.text_area("3. 是否有发现任何异常之处？(选填)")
        
        behavior_map = {"从未": 0, "偶尔查阅常识": 1, "深度验证参数/法案": 2}
        trust_map = {"无影响": 1, "轻微": 2, "中立": 3, "显著": 4, "决定性": 5}

        if st.form_submit_button("提交反馈并解锁真相"):
            with st.spinner("正在加密回传数据，请稍候..."):
                try:
                    # 关键补丁：ttl=0 防止云端缓存覆盖新数据
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    try:
                        existing_data = conn.read(worksheet="Sheet1", ttl=0) 
                        existing_data = existing_data.dropna(how="all")
                    except:
                        existing_data = pd.DataFrame()
                        
                    for d in st.session_state.decisions:
                        d.update({
                            "search_behavior": behavior_map[behavior_text], 
                            "trust_level": trust_map[trust_text], 
                            "feedback": suspicion
                        })
                    
                    new_data = pd.DataFrame(st.session_state.decisions)
                    updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                    
                    conn.update(worksheet="Sheet1", data=updated_df)
                except Exception as e:
                    st.toast("数据同步可能出现延迟，但不影响您的实验进程。", icon="⚠️")
                    print(e)
            
            st.session_state.step = "debrief"
            st.rerun()

# --- 6. 步骤 4：真相告知 ---
elif st.session_state.step == "debrief":
    st.balloons()
    st.title("🎉 实验已完成，非常感谢您的参与！")
    
    with st.expander("🎓 关于本研究的机密说明 (点击展开)", expanded=True):
        st.write("""
        本研究旨在评估工程师、高管与学生在面对 Agentic-AI 时的‘信任校准’机制。
        **为了测试极限情况，部分 AI 建议（如特定法案的冲突或违规预警）是我们故意植入的算法幻觉。**
        
        您的直觉判断和决策依据将对我们探索【可信工业 AI】的治理框架提供极大的帮助。
        为了不影响后续同事的判断，**请对以上陷阱细节保密**。
        """)
    
    st.success("您的数据已加密上传完毕。现在您可以安全地关闭此窗口了。祝您工作顺利！")
