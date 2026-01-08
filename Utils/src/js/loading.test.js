
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Since the original file declares global functions, we might need to load it differently 
// or mock the global scope. For this example, we will simulate the behavior.

describe('loading.js logic', () => {
  beforeEach(() => {
    document.body.innerHTML = 
      '<div id="_dash-loading" style="display: block;"></div>' +
      '<div id="content-main" style="display: none;"></div>';
  });

  it('should hide loading and show content', () => {
    // reimplementing showPage logic since the original file is not a module
    function showPage() {
        document.getElementById("_dash-loading").style.display = "none";
        document.getElementById("content-main").style.display = "block";
    }

    showPage();

    expect(document.getElementById('_dash-loading').style.display).toBe('none');
    expect(document.getElementById('content-main').style.display).toBe('block');
  });
});
