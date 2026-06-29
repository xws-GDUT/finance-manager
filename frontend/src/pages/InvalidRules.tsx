import RuleManager from '../components/RuleManager';
import {
  fetchInvalidRules, createInvalidRule, updateInvalidRule, deleteInvalidRule,
  testInvalidRule, applyInvalidRules,
} from '../api';

export default function InvalidRules() {
  return (
    <RuleManager
      type="invalid"
      title="无效规则（黑名单）"
      fetchFn={fetchInvalidRules}
      createFn={createInvalidRule}
      updateFn={updateInvalidRule}
      deleteFn={deleteInvalidRule}
      testFn={testInvalidRule}
      applyFn={applyInvalidRules}
    />
  );
}
