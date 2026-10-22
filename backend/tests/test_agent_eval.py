from agent_eval.eval_runner import AgentEvaluationRunner


def test_agent_evaluation_suite_benchmark():
    runner = AgentEvaluationRunner()
    try:
        summary = runner.run_all()
        assert summary["total_tests"] == 10
        assert summary["failed_tests"] == 0
        assert summary["pass_rate_percent"] == 100.0
    finally:
        runner.close()
