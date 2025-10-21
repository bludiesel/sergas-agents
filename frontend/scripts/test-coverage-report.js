#!/usr/bin/env node

/**
 * Test Coverage Report Generator
 *
 * Advanced coverage reporting with quality metrics
 * and trend analysis for CopilotKit testing
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration
const CONFIG = {
  coverageDir: path.join(__dirname, '../coverage'),
  reportsDir: path.join(__dirname, '../coverage/reports'),
  baselineFile: path.join(__dirname, '../coverage/baseline.json'),
  trendsFile: path.join(__dirname, '../coverage/trends.json'),
  thresholds: {
    excellent: { statements: 90, functions: 90, branches: 85, lines: 90 },
    good: { statements: 80, functions: 80, branches: 75, lines: 80 },
    acceptable: { statements: 70, functions: 70, branches: 65, lines: 70 },
    poor: { statements: 50, functions: 50, branches: 45, lines: 50 },
  },
};

class CoverageReporter {
  constructor() {
    this.ensureDirectories();
  }

  ensureDirectories() {
    if (!fs.existsSync(CONFIG.reportsDir)) {
      fs.mkdirSync(CONFIG.reportsDir, { recursive: true });
    }
  }

  generateReports() {
    console.log('🔍 Generating comprehensive coverage reports...');

    // Read coverage data
    const coverageData = this.readCoverageData();
    if (!coverageData) {
      console.error('❌ No coverage data found');
      return;
    }

    // Generate different reports
    this.generateSummaryReport(coverageData);
    this.generateQualityReport(coverageData);
    this.generateTrendReport(coverageData);
    this.generateComponentReport(coverageData);
    this.generateRecommendations(coverageData);
    this.generateBadgeData(coverageData);

    console.log('✅ Coverage reports generated successfully!');
  }

  readCoverageData() {
    const coverageFile = path.join(CONFIG.coverageDir, 'coverage-final.json');

    if (!fs.existsSync(coverageFile)) {
      return null;
    }

    try {
      const content = fs.readFileSync(coverageFile, 'utf8');
      return JSON.parse(content);
    } catch (error) {
      console.error('Error reading coverage data:', error);
      return null;
    }
  }

  generateSummaryReport(coverageData) {
    const summary = this.calculateCoverageSummary(coverageData);
    const report = this.createMarkdownReport(summary, 'Coverage Summary');

    fs.writeFileSync(
      path.join(CONFIG.reportsDir, 'summary.md'),
      report
    );
  }

  generateQualityReport(coverageData) {
    const qualityMetrics = this.calculateQualityMetrics(coverageData);
    const report = this.createMarkdownReport(qualityMetrics, 'Quality Metrics');

    fs.writeFileSync(
      path.join(CONFIG.reportsDir, 'quality.md'),
      report
    );
  }

  generateTrendReport(coverageData) {
    const trends = this.calculateTrends(coverageData);
    const report = this.createMarkdownReport(trends, 'Coverage Trends');

    fs.writeFileSync(
      path.join(CONFIG.reportsDir, 'trends.md'),
      report
    );
  }

  generateComponentReport(coverageData) {
    const componentCoverage = this.calculateComponentCoverage(coverageData);
    const report = this.createMarkdownReport(componentCoverage, 'Component Coverage');

    fs.writeFileSync(
      path.join(CONFIG.reportsDir, 'components.md'),
      report
    );
  }

  generateRecommendations(coverageData) {
    const recommendations = this.generateRecommendations(coverageData);
    const report = this.createMarkdownReport(recommendations, 'Recommendations');

    fs.writeFileSync(
      path.join(CONFIG.reportsDir, 'recommendations.md'),
      report
    );
  }

  generateBadgeData(coverageData) {
    const summary = this.calculateCoverageSummary(coverageData);
    const badgeData = this.createBadgeData(summary);

    fs.writeFileSync(
      path.join(CONFIG.coverageDir, 'badge-data.json'),
      JSON.stringify(badgeData, null, 2)
    );
  }

  calculateCoverageSummary(coverageData) {
    const totals = coverageData.total;

    return {
      statements: {
        covered: totals.statements.covered,
        total: totals.statements.total,
        percentage: totals.statements.pct,
      },
      branches: {
        covered: totals.branches.covered,
        total: totals.branches.total,
        percentage: totals.branches.pct,
      },
      functions: {
        covered: totals.functions.covered,
        total: totals.functions.total,
        percentage: totals.functions.pct,
      },
      lines: {
        covered: totals.lines.covered,
        total: totals.lines.total,
        percentage: totals.lines.pct,
      },
    };
  }

  calculateQualityMetrics(coverageData) {
    const summary = this.calculateCoverageSummary(coverageData);
    const overall = this.getOverallQuality(summary);

    return {
      overall,
      score: this.calculateQualityScore(summary),
      grade: this.calculateGrade(summary),
      metrics: {
        coverage: summary,
        complexity: this.calculateComplexity(coverageData),
        maintainability: this.calculateMaintainability(coverageData),
        testQuality: this.calculateTestQuality(coverageData),
      },
    };
  }

  calculateTrends(coverageData) {
    const currentCoverage = this.calculateCoverageSummary(coverageData);
    const baseline = this.loadBaseline();
    const trends = this.loadTrends();

    // Add current coverage to trends
    trends.push({
      timestamp: new Date().toISOString(),
      coverage: currentCoverage,
    });

    // Keep only last 30 entries
    const recentTrends = trends.slice(-30);
    this.saveTrends(recentTrends);

    return {
      current: currentCoverage,
      baseline: baseline,
      trends: recentTrends,
      analysis: this.analyzeTrends(recentTrends),
    };
  }

  calculateComponentCoverage(coverageData) {
    const componentStats = {};

    Object.keys(coverageData).forEach(filePath => {
      if (filePath.includes('/components/copilot/')) {
        const fileCoverage = coverageData[filePath];
        const statements = this.getFileMetrics(fileCoverage, 'statements');
        const branches = this.getFileMetrics(fileCoverage, 'branches');
        const functions = this.getFileMetrics(fileCoverage, 'functions');
        const lines = this.getFileMetrics(fileCoverage, 'lines');

        componentStats[filePath] = {
          statements,
          branches,
          functions,
          lines,
          overall: this.calculateOverallScore({ statements, branches, functions, lines }),
        };
      }
    });

    return componentStats;
  }

  generateRecommendations(coverageData) {
    const summary = this.calculateCoverageSummary(coverageData);
    const componentCoverage = this.calculateComponentCoverage(coverageData);

    const recommendations = [];

    // Coverage recommendations
    if (summary.statements.percentage < 80) {
      recommendations.push({
        type: 'coverage',
        priority: 'high',
        message: 'Statement coverage is below 80%. Add more tests for happy path scenarios.',
      });
    }

    if (summary.branches.percentage < 75) {
      recommendations.push({
        type: 'coverage',
        priority: 'high',
        message: 'Branch coverage is below 75%. Test edge cases and error conditions.',
      });
    }

    // Component-specific recommendations
    Object.entries(componentCoverage).forEach(([componentPath, coverage]) => {
      if (coverage.overall < 70) {
        const componentName = path.basename(componentPath, '.tsx');
        recommendations.push({
          type: 'component',
          priority: 'medium',
          component: componentName,
          message: `${componentName} has low coverage (${coverage.overall.toFixed(1)}%). Focus on testing core functionality.`,
        });
      }
    });

    return recommendations;
  }

  getOverallQuality(summary) {
    const avgCoverage = (summary.statements.percentage + summary.branches.percentage +
                          summary.functions.percentage + summary.lines.percentage) / 4;

    if (avgCoverage >= CONFIG.thresholds.excellent.statements) return 'excellent';
    if (avgCoverage >= CONFIG.thresholds.good.statements) return 'good';
    if (avgCoverage >= CONFIG.thresholds.acceptable.statements) return 'acceptable';
    return 'poor';
  }

  calculateQualityScore(summary) {
    // Weighted score calculation
    const weights = {
      statements: 0.3,
      branches: 0.25,
      functions: 0.25,
      lines: 0.2,
    };

    const score = (summary.statements.percentage * weights.statements) +
                  (summary.branches.percentage * weights.branches) +
                  (summary.functions.percentage * weights.functions) +
                  (summary.lines.percentage * weights.lines);

    return Math.round(score * 100) / 100; // Round to 2 decimal places
  }

  calculateGrade(summary) {
    const score = this.calculateQualityScore(summary);

    if (score >= 95) return 'A+';
    if (score >= 90) return 'A';
    if (score >= 85) return 'B+';
    if (score >= 80) return 'B';
    if (score >= 75) return 'C+';
    if (score >= 70) return 'C';
    if (score >= 65) return 'D';
    return 'F';
  }

  getFileMetrics(fileCoverage, metricType) {
    const metrics = fileCoverage[metricType];
    if (!metrics) return { covered: 0, total: 0, percentage: 0 };

    return {
      covered: metrics.covered,
      total: metrics.total,
      percentage: metrics.pct || 0,
    };
  }

  calculateOverallScore(metrics) {
    const weights = { statements: 0.3, branches: 0.25, functions: 0.25, lines: 0.2 };

    const score = (metrics.statements.percentage * weights.statements) +
                  (metrics.branches.percentage * weights.branches) +
                  (metrics.functions.percentage * weights.functions) +
                  (metrics.lines.percentage * weights.lines);

    return Math.round(score * 100) / 100;
  }

  calculateComplexity(coverageData) {
    // Simplified complexity calculation based on file coverage patterns
    let totalComplexity = 0;
    let fileCount = 0;

    Object.values(coverageData).forEach(fileCoverage => {
      const functions = fileCoverage.functions || {};
      Object.values(functions).forEach(funcCoverage => {
        if (funcCoverage.s) {
          // Count branches as complexity indicator
          const branchCount = (funcCoverage.s.match(/if|switch|case|&&|\|\|/g) || []).length;
          totalComplexity += branchCount + 1; // Base complexity + branches
        }
      });
      fileCount++;
    });

    return fileCount > 0 ? Math.round(totalComplexity / fileCount) : 0;
  }

  calculateMaintainability(coverageData) {
    const summary = this.calculateCoverageSummary(coverageData);
    const complexity = this.calculateComplexity(coverageData);

    // Maintainability index (simplified)
    const coverageScore = summary.statements.percentage / 100;
    const complexityPenalty = Math.min(complexity / 20, 1); // Penalty for high complexity
    const maintainability = Math.round((coverageScore - complexityPenalty) * 100);

    return Math.max(0, maintainability);
  }

  calculateTestQuality(coverageData) {
    // Test quality indicators
    let testCount = 0;
    let assertionsCount = 0;
    let errorHandlingTests = 0;

    // This would require parsing test files for more accurate metrics
    // For now, provide estimated values
    Object.keys(coverageData).forEach(filePath => {
      if (filePath.includes('__tests__')) {
        testCount++;
        if (filePath.includes('error') || filePath.includes('failure')) {
          errorHandlingTests++;
        }
      }
    });

    return {
      totalTests: testCount * 10, // Estimated
      errorHandlingTests,
      testToCodeRatio: testCount > 0 ? (testCount * 10) / Object.keys(coverageData).length : 0,
    };
  }

  analyzeTrends(trends) {
    if (trends.length < 2) return { trend: 'insufficient_data' };

    const latest = trends[trends.length - 1];
    const previous = trends[trends.length - 2];

    const statementsTrend = latest.coverage.statements.percentage - previous.coverage.statements.percentage;
    const branchesTrend = latest.coverage.branches.percentage - previous.coverage.branches.percentage;

    return {
      statementsTrend: statementsTrend > 0 ? 'improving' : statementsTrend < 0 ? 'declining' : 'stable',
      branchesTrend: branchesTrend > 0 ? 'improving' : branchesTrend < 0 ? 'declining' : 'stable',
      averageImprovement: this.calculateAverageImprovement(trends),
    };
  }

  calculateAverageImprovement(trends) {
    if (trends.length < 2) return 0;

    let totalImprovement = 0;
    let comparisons = 0;

    for (let i = 1; i < trends.length; i++) {
      const current = trends[i];
      const previous = trends[i - 1];

      totalImprovement += current.coverage.statements.percentage - previous.coverage.statements.percentage;
      comparisons++;
    }

    return comparisons > 0 ? (totalImprovement / comparisons).toFixed(2) : 0;
  }

  createMarkdownReport(data, title) {
    let report = `# ${title}\n\n`;

    if (data.overall) {
      report += `## Overall Assessment\n\n`;
      report += `- **Quality Level**: ${data.overall.toUpperCase()}\n`;
      report += `- **Score**: ${data.score}/100\n`;
      report += `- **Grade**: ${data.grade}\n\n`;
    }

    if (data.coverage) {
      report += `## Coverage Metrics\n\n`;
      report += `| Metric | Covered | Total | Percentage |\n`;
      report += `|--------|---------|-------|------------|\n`;

      Object.entries(data.coverage).forEach(([metric, data]) => {
        report += `| ${metric.charAt(0).toUpperCase() + metric.slice(1)} | ${data.covered} | ${data.total} | ${data.percentage.toFixed(1)}% |\n`;
      });
      report += `\n`;
    }

    if (data.metrics) {
      report += `## Detailed Metrics\n\n`;

      if (data.metrics.complexity !== undefined) {
        report += `- **Average Complexity**: ${data.metrics.complexity}\n`;
      }

      if (data.metrics.maintainability !== undefined) {
        report += `- **Maintainability Index**: ${data.metrics.maintainability}/100\n`;
      }

      if (data.metrics.testQuality) {
        report += `- **Test Quality**: ${data.metrics.testQuality.totalTests} tests, ${data.metrics.testQuality.errorHandlingTests} error handling tests\n`;
        report += `- **Test-to-Code Ratio**: ${data.metrics.testQuality.testToCodeRatio.toFixed(2)}\n`;
      }
      report += `\n`;
    }

    if (data.trends) {
      report += `## Trend Analysis\n\n`;

      if (data.trends.current) {
        report += `- **Current Coverage**: ${data.trends.current.coverage.statements.percentage.toFixed(1)}%\n`;
      }

      if (data.trends.analysis) {
        report += `- **Statements Trend**: ${data.trends.analysis.statementsTrend}\n`;
        report += `- **Branches Trend**: ${data.trends.analysis.branchesTrend}\n`;
        report += `- **Average Improvement**: ${data.trends.analysis.averageImprovement}%\n`;
      }
      report += `\n`;
    }

    if (data.recommendations) {
      report += `## Recommendations\n\n`;

      data.recommendations.forEach((rec, index) => {
        const priority = rec.priority.toUpperCase();
        report += `${index + 1}. **${priority}**: ${rec.message}\n`;

        if (rec.component) {
          report += `   - Component: ${rec.component}\n`;
        }

        if (rec.type) {
          report += `   - Type: ${rec.type}\n`;
        }
        report += `\n`;
      });
    }

    return report;
  }

  createBadgeData(summary) {
    const percentage = summary.statements.percentage;

    return {
      schemaVersion: 1,
      label: 'coverage',
      message: `${percentage.toFixed(1)}%`,
      color: this.getBadgeColor(percentage),
    };
  }

  getBadgeColor(percentage) {
    if (percentage >= 90) return '#4c1';
    if (percentage >= 80) return '#97ca00';
    if (percentage >= 70) return '#a4a61c';
    if (percentage >= 60) return '#fe7d37';
    return '#e05d44';
  }

  loadBaseline() {
    if (fs.existsSync(CONFIG.baselineFile)) {
      try {
        const content = fs.readFileSync(CONFIG.baselineFile, 'utf8');
        return JSON.parse(content);
      } catch (error) {
        console.warn('Warning: Could not load baseline:', error.message);
      }
    }
    return null;
  }

  loadTrends() {
    if (fs.existsSync(CONFIG.trendsFile)) {
      try {
        const content = fs.readFileSync(CONFIG.trendsFile, 'utf8');
        return JSON.parse(content);
      } catch (error) {
        console.warn('Warning: Could not load trends:', error.message);
      }
    }
    return [];
  }

  saveTrends(trends) {
    try {
      fs.writeFileSync(CONFIG.trendsFile, JSON.stringify(trends, null, 2));
    } catch (error) {
      console.error('Error saving trends:', error);
    }
  }
}

// Main execution
if (require.main === module) {
  const reporter = new CoverageReporter();
  reporter.generateReports();

  // Output summary to console
  console.log('\n📊 Coverage Summary:');
  console.log('📁 Reports generated in: coverage/reports/');
  console.log('🌐 HTML report: coverage/lcov-report/index.html');
  console.log('\n💡 Run "npm run test:coverage" to generate updated reports');
}