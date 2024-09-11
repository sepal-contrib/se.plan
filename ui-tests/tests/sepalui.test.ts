// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { expect, test } from '@playwright/test';
import { addBenchmarkToTest } from './utils';

test.describe('Voila performance Tests', () => {
  test.beforeEach(({ page }) => {
    page.setDefaultTimeout(120000);
  });
  test.afterEach(async ({ page, browserName }) => {
    await page.close({ runBeforeUnload: true });
  });

  test('Render and benchmark ui.ipynb', async ({
    page,
    browserName
  }, testInfo) => {
    const notebookName = 'ui';
    const testFunction = async () => {
      await page.goto(`/voila/render/${notebookName}.ipynb`);
    };
    await addBenchmarkToTest(notebookName, testFunction, testInfo, browserName);
    expect(await page.screenshot()).toMatchSnapshot(`${notebookName}.png`);
  });

});
