# UX Consolidation Testing Guide

This guide covers testing the consolidated UX changes for the route-buncher application.

## Test Environment Setup

1. **Backup your .env file** (optional but recommended)
2. **Have sample CSV data ready** for testing
3. **Check API keys are configured** (for non-test mode testing):
   - `GOOGLE_MAPS_API_KEY` (required for real geocoding)
   - `ANTHROPIC_API_KEY` (optional, for AI features)

---

## Test Matrix

| Mode | Test Mode | Expected Behavior |
|------|-----------|-------------------|
| Single Window | OFF | Google Maps polylines, AI validation, costs money |
| Single Window | ON | Mock geocoding, mock AI, zero cost |
| Multi-Window | OFF | Google Maps polylines (all routes), AI per window, costs money |
| Multi-Window | ON | Mock geocoding, mock AI, zero cost |

---

## Test 1: Test Mode Verification ✅

**Objective**: Verify test mode skips both Maps API and AI API

**Steps**:
1. Start the app: `streamlit run app.py`
2. In sidebar, enable "🧪 Test Mode (Skip API Calls)" checkbox
3. Upload a CSV file with orders
4. Click "🚀 Run Optimization"

**Expected Results**:
- ⚠️ Warning banner shows: "Test Mode Active - Using mock data for Maps and AI"
- No "✅ AI Features Enabled" message (AI is disabled in test mode)
- Map renders with mock geocoding data
- AI validation shows: "✅ Route validation (Test Mode - Mock Response)"
- Order reasons are generic: "Test mode - Order kept in optimized route"
- **Check API consoles**: Zero calls to Google Maps API and Anthropic API

**Pass Criteria**: ✅ No API costs incurred, mock data displayed

---

## Test 2: Single Window Mode with AI ✅

**Objective**: Verify single window optimization works with AI features

**Steps**:
1. Disable test mode checkbox
2. Ensure `ANTHROPIC_API_KEY` is configured in .env
3. Select "One window" mode
4. Choose a delivery window from dropdown
5. Click "🚀 Run Optimization"

**Expected Results**:
- ✅ Green success banner: "AI Features Enabled"
- Map shows Google Maps polylines (actual road routes, not straight lines)
- Numbered stop markers (1, 2, 3...) with green circles
- AI validation message is detailed and specific (not generic)
- Order disposition reasons are context-aware
- Chat assistant is available in sidebar
- All 4 cuts (Cut 1, 2, 3, 4) render correctly

**Pass Criteria**: ✅ Detailed AI analysis, Google Maps routes, numbered markers

---

## Test 3: Single Window Mode in Test Mode ✅

**Objective**: Verify single window works without API costs

**Steps**:
1. Enable test mode checkbox
2. Select "One window" mode
3. Choose a delivery window
4. Click "🚀 Run Optimization"

**Expected Results**:
- ⚠️ Warning: "Test Mode Active"
- Map shows with mock data (straight-line estimates)
- Generic order reasons
- Mock AI validation
- All UI elements render correctly
- **Zero API costs**

**Pass Criteria**: ✅ Functional without API costs

---

## Test 4: Multi-Window Mode with AI ✅

**Objective**: Verify multi-window optimization with enhanced UX

**Steps**:
1. Disable test mode checkbox
2. Ensure `ANTHROPIC_API_KEY` is configured
3. Select "Full day" mode
4. Configure capacities for multiple windows
5. Click "🚀 Run Optimization"

**Expected Results**:
- ✅ "AI Features Enabled" message shows
- **Global Map**:
  - Shows all routes with different colors
  - Uses Google Maps polylines (actual roads)
  - Each route has numbered stops (1, 2, 3...)
  - Legend shows color mapping to windows
- **Per-Window Expanders** (NEW!):
  - KPI dashboard with 4 metrics:
    - Orders Kept
    - Capacity Used (with percentage)
    - Route Time (with percentage of window)
    - Efficiency (orders/hr)
  - Individual window map showing just that window's route
  - AI validation per window (if AI enabled)
  - Order tables (KEEP, EARLY, RESCHEDULE, CANCEL)
- All windows render correctly

**Pass Criteria**: ✅ Google Maps polylines on global map, per-window KPIs and maps, AI per window

---

## Test 5: Multi-Window Mode in Test Mode ✅

**Objective**: Verify multi-window works without API costs

**Steps**:
1. Enable test mode checkbox
2. Select "Full day" mode
3. Configure capacities
4. Click "🚀 Run Optimization"

**Expected Results**:
- ⚠️ "Test Mode Active" warning
- Mock data for all windows
- Generic AI responses
- All windows render correctly
- **Zero API costs**

**Pass Criteria**: ✅ Functional without API costs

---

## Test 6: UI Consistency Check ✅

**Objective**: Verify consistent UX across modes

**Steps**:
1. Run optimization in single window mode
2. Run optimization in multi-window mode
3. Compare displays

**Expected Results**:
- Same button colors and styles
- Same KPI metric formats
- Same map styling (Google Maps tiles, numbered markers)
- Same color scheme for order statuses
- Consistent error messages
- Same status indicators

**Pass Criteria**: ✅ UI feels consistent across both modes

---

## Test 7: API Key Missing ✅

**Objective**: Verify behavior when no Anthropic API key

**Steps**:
1. Rename `ANTHROPIC_API_KEY` in .env (or remove it)
2. Disable test mode
3. Run optimization

**Expected Results**:
- ℹ️ Blue info banner: "AI Disabled (No API Key)"
- Optimization still works
- Generic order reasons instead of AI explanations
- No chat assistant available
- No AI validation messages

**Pass Criteria**: ✅ App works without AI, clear messaging about missing key

---

## Test 8: Button Simplification ✅

**Objective**: Verify old dual buttons are replaced

**Steps**:
1. Check sidebar for run buttons

**Expected Results**:
- ❌ No "🚀 Run (with AI)" button
- ❌ No "⚡ Run (no AI)" button
- ✅ Single "🚀 Run Optimization" button
- ✅ Test mode checkbox above button
- ✅ AI status indicator shows before button

**Pass Criteria**: ✅ Single button interface, clear status

---

## Test 9: Map Quality Comparison ✅

**Objective**: Verify multi-window maps match single-window quality

**Before (Old Multi-Window)**:
- OpenStreetMap tiles
- Straight lines between points
- Simple colored circle markers
- No stop numbers

**After (New Multi-Window)**:
- Google Maps tiles
- Actual road route polylines
- Numbered stop markers
- Rich tooltips with window info
- Legend showing color mapping

**Steps**:
1. Run multi-window optimization with test mode OFF
2. Check global map quality
3. Check individual window maps in expanders

**Pass Criteria**: ✅ Maps use Google tiles, show road routes, have numbered markers

---

## Test 10: Error Handling ✅

**Objective**: Verify graceful error handling

**Steps**:
1. Upload invalid CSV (missing columns)
2. Upload CSV with bad addresses
3. Try to run with no data

**Expected Results**:
- Clear error messages
- No crashes
- Helpful suggestions for fixing issues
- App remains usable after errors

**Pass Criteria**: ✅ Errors handled gracefully, no crashes

---

## Regression Testing ✅

**Objective**: Verify existing functionality still works

**Test existing features**:
- [ ] Dispatcher Sandbox (Cut 4) in single window mode
- [ ] CSV upload and parsing
- [ ] Service time configuration (fixed vs smart)
- [ ] Priority customer handling in multi-window
- [ ] Order filtering and validation
- [ ] Export functionality (if applicable)

**Pass Criteria**: ✅ All existing features work as before

---

## Performance Testing 📊

**Objective**: Check performance hasn't degraded

**Steps**:
1. Load large CSV (100+ orders)
2. Run optimization in both modes
3. Time the operations

**Expected**:
- Test mode: <5 seconds
- Live mode (with APIs): <30 seconds (depends on API response times)
- No significant performance degradation vs. old version

**Pass Criteria**: ✅ Performance acceptable

---

## API Cost Verification 💰

**CRITICAL**: Verify test mode actually saves costs

**Steps**:
1. Note current API usage in Google Cloud Console and Anthropic Console
2. Run 5 optimizations in test mode (both single and multi-window)
3. Check API consoles again

**Expected**:
- Google Maps API: **Zero additional calls**
- Anthropic API: **Zero additional calls**
- Usage numbers unchanged

**Pass Criteria**: ✅ No API costs in test mode

---

## Final Checklist ✅

Before considering testing complete, verify:

- [x] Syntax validation passed (no Python errors)
- [ ] Test mode works (zero API costs)
- [ ] Single button replaces dual buttons
- [ ] AI status indicators show correctly
- [ ] Single window maps use Google polylines
- [ ] Multi-window global map uses Google polylines
- [ ] Multi-window per-window maps render
- [ ] Per-window KPI dashboards show
- [ ] AI validation per window (when enabled)
- [ ] Numbered stop markers in all maps
- [ ] Legend shows on multi-window global map
- [ ] Chat assistant works (when AI enabled)
- [ ] No crashes or major bugs
- [ ] Documentation updated (CLAUDE.md)

---

## Known Issues / Limitations

*(Document any issues found during testing here)*

- None found yet

---

## Rollback Plan

If critical issues are found:

1. **Git checkout previous commit**:
   ```bash
   git log --oneline  # Find commit before UX consolidation
   git checkout <commit-hash>
   ```

2. **Revert specific files** if only partial rollback needed:
   ```bash
   git checkout HEAD~1 app.py config.py chat_assistant.py geocoder.py
   ```

3. **Test old version** to confirm it works
4. **Document issues** to fix before re-attempting

---

## Success Criteria Summary

All tests pass when:
✅ Test mode successfully skips both Maps and AI APIs
✅ Single button interface is clear and functional
✅ Multi-window maps show Google Maps road routes with numbered stops
✅ Per-window detailed views display KPIs, maps, and AI validation
✅ Consistent UX between single and multi-window modes
✅ No regressions in existing functionality
✅ Zero API costs in test mode verified
✅ Documentation reflects new UX

---

**Last Updated**: 2026-02-16
**Tested By**: ___________
**Test Results**: ___________
