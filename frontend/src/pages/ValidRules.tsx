import RuleManager from '../components/RuleManager';
import {
  fetchValidRules, createValidRule, updateValidRule, deleteValidRule,
  testValidRule, applyValidRules, createDefaultValidRules,
} from '../api';

export default function ValidRules() {
  return (
    <RuleManager
      type="valid"
      title="有效规则（白名单）"
      fetchFn={fetchValidRules}
      createFn={createValidRule}
      updateFn={updateValidRule}
      deleteFn={deleteValidRule}
      testFn={testValidRule}
      applyFn={applyValidRules}
      createDefaultsFn={createDefaultValidRules}
    />
  );
}
