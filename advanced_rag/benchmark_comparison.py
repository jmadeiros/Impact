"""
Objective Performance Comparison Framework
Compares Advanced RAG vs Simple RAG on specific metrics
"""
import os
import sys
sys.path.append('..')

import time
import json
from typing import List, Dict, Any, Tuple
from datetime import datetime
import statistics

class RAGBenchmark:
    def __init__(self):
        self.test_queries = self.create_test_query_suite()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'test_queries': [],
            'summary_metrics': {},
            'recommendations': []
        }
    
    def create_test_query_suite(self) -> List[Dict[str, Any]]:
        """Create comprehensive test query suite with expected characteristics"""
        return [
            # ACCURACY TESTS - Conceptual/Semantic Queries
            {
                'query': 'How do creative programs like filmmaking build confidence in young people?',
                'category': 'accuracy',
                'difficulty': 'high',
                'expected_themes': ['confidence', 'creative', 'filmmaking', 'self-esteem'],
                'semantic_complexity': 'high'
            },
            {
                'query': 'What evidence shows that these programs help participants make social connections?',
                'category': 'accuracy', 
                'difficulty': 'high',
                'expected_themes': ['friends', 'social', 'connections', 'team'],
                'semantic_complexity': 'high'
            },
            {
                'query': 'Show me stories about young people overcoming challenges',
                'category': 'accuracy',
                'difficulty': 'medium',
                'expected_themes': ['challenges', 'overcome', 'resilience', 'difficult'],
                'semantic_complexity': 'medium'
            },
            
            # ROBUSTNESS TESTS - Varied Phrasing
            {
                'query': 'confidence building',
                'category': 'robustness',
                'difficulty': 'low',
                'expected_themes': ['confidence', 'self-esteem', 'proud'],
                'semantic_complexity': 'low'
            },
            {
                'query': 'How did the program boost self-esteem?',
                'category': 'robustness',
                'difficulty': 'medium',
                'expected_themes': ['confidence', 'self-esteem', 'proud'],
                'semantic_complexity': 'medium'
            },
            {
                'query': 'Tell me about participants gaining belief in themselves',
                'category': 'robustness',
                'difficulty': 'high',
                'expected_themes': ['confidence', 'self-esteem', 'believe'],
                'semantic_complexity': 'high'
            },
            
            # LATENCY TESTS - Performance Under Load
            {
                'query': 'What impact does YCUK have?',
                'category': 'latency',
                'difficulty': 'low',
                'expected_themes': ['YCUK', 'impact'],
                'semantic_complexity': 'low'
            },
            {
                'query': 'Compare the effectiveness of different youth programs',
                'category': 'latency',
                'difficulty': 'high',
                'expected_themes': ['compare', 'effectiveness', 'programs'],
                'semantic_complexity': 'high'
            },
            
            # EDGE CASES - System Stress Tests
            {
                'query': 'What negative experiences or criticisms were mentioned?',
                'category': 'edge_case',
                'difficulty': 'high',
                'expected_themes': ['negative', 'criticism', 'problems'],
                'semantic_complexity': 'medium'
            },
            {
                'query': 'How do participants feel about their future prospects after the program?',
                'category': 'edge_case',
                'difficulty': 'high',
                'expected_themes': ['future', 'prospects', 'aspirations'],
                'semantic_complexity': 'high'
            }
        ]
    
    def evaluate_accuracy(self, query_info: Dict, simple_result: Dict, advanced_result: Dict) -> Dict[str, float]:
        """Evaluate accuracy metrics"""
        metrics = {}
        
        # Theme coverage - how many expected themes are found
        expected_themes = query_info['expected_themes']
        
        def count_theme_coverage(result, themes):
            answer_text = result.get('answer', '').lower()
            evidence_text = ' '.join([
                ev.get('story_text', ev.get('response_value', '')) 
                for ev in result.get('source_evidence', result.get('source_documents', []))
            ]).lower()
            
            full_text = f"{answer_text} {evidence_text}"
            return sum(1 for theme in themes if theme in full_text)
        
        simple_coverage = count_theme_coverage(simple_result, expected_themes)
        advanced_coverage = count_theme_coverage(advanced_result, expected_themes)
        
        metrics['simple_theme_coverage'] = simple_coverage / len(expected_themes)
        metrics['advanced_theme_coverage'] = advanced_coverage / len(expected_themes)
        metrics['theme_coverage_improvement'] = metrics['advanced_theme_coverage'] - metrics['simple_theme_coverage']
        
        # Evidence relevance - quality of retrieved documents
        simple_evidence_count = simple_result.get('evidence_count', 0)
        advanced_evidence_count = advanced_result.get('evidence_count', 0)
        
        metrics['simple_evidence_count'] = simple_evidence_count
        metrics['advanced_evidence_count'] = advanced_evidence_count
        metrics['evidence_count_ratio'] = advanced_evidence_count / max(simple_evidence_count, 1)
        
        # Answer completeness
        simple_answer_length = len(simple_result.get('answer', ''))
        advanced_answer_length = len(advanced_result.get('answer', ''))
        
        metrics['simple_answer_length'] = simple_answer_length
        metrics['advanced_answer_length'] = advanced_answer_length
        metrics['answer_length_ratio'] = advanced_answer_length / max(simple_answer_length, 1)
        
        return metrics
    
    def evaluate_robustness(self, query_info: Dict, simple_result: Dict, advanced_result: Dict) -> Dict[str, float]:
        """Evaluate robustness metrics"""
        metrics = {}
        
        # Error handling
        simple_has_error = 'error' in simple_result
        advanced_has_error = 'error' in advanced_result
        
        metrics['simple_error_rate'] = 1.0 if simple_has_error else 0.0
        metrics['advanced_error_rate'] = 1.0 if advanced_has_error else 0.0
        metrics['error_rate_improvement'] = metrics['simple_error_rate'] - metrics['advanced_error_rate']
        
        # Response consistency (non-empty, meaningful responses)
        simple_meaningful = simple_result.get('evidence_count', 0) > 0 and len(simple_result.get('answer', '')) > 50
        advanced_meaningful = advanced_result.get('evidence_count', 0) > 0 and len(advanced_result.get('answer', '')) > 50
        
        metrics['simple_meaningful_response'] = 1.0 if simple_meaningful else 0.0
        metrics['advanced_meaningful_response'] = 1.0 if advanced_meaningful else 0.0
        metrics['meaningful_response_improvement'] = metrics['advanced_meaningful_response'] - metrics['simple_meaningful_response']
        
        return metrics
    
    def evaluate_latency(self, simple_time: float, advanced_time: float) -> Dict[str, float]:
        """Evaluate latency metrics"""
        return {
            'simple_response_time': simple_time,
            'advanced_response_time': advanced_time,
            'latency_ratio': advanced_time / max(simple_time, 0.001),
            'latency_acceptable': 1.0 if advanced_time < 10.0 else 0.0  # 10 second threshold
        }
    
    def run_single_comparison(self, query_info: Dict) -> Dict[str, Any]:
        """Run comparison for a single query"""
        query = query_info['query']
        print(f"\n🔍 Testing: '{query}'")
        print(f"   Category: {query_info['category']}, Difficulty: {query_info['difficulty']}")
        
        results = {
            'query_info': query_info,
            'simple_result': {},
            'advanced_result': {},
            'metrics': {},
            'execution_times': {}
        }
        
        # Test Simple System
        try:
            from simple_rag_system import SimpleRAGSystem
            simple_system = SimpleRAGSystem()
            
            start_time = time.time()
            simple_result = simple_system.process_query(query)
            simple_time = time.time() - start_time
            
            results['simple_result'] = simple_result
            results['execution_times']['simple'] = simple_time
            print(f"   Simple: {simple_result.get('evidence_count', 0)} evidence, {simple_time:.2f}s")
            
        except Exception as e:
            print(f"   ❌ Simple system failed: {str(e)}")
            results['simple_result'] = {'error': str(e), 'evidence_count': 0, 'answer': ''}
            results['execution_times']['simple'] = 999.0
        
        # Test Advanced System
        try:
            from langchain_rag import AdvancedRAGSystem
            advanced_system = AdvancedRAGSystem()
            
            start_time = time.time()
            advanced_result = advanced_system.query(query)
            advanced_time = time.time() - start_time
            
            results['advanced_result'] = advanced_result
            results['execution_times']['advanced'] = advanced_time
            print(f"   Advanced: {advanced_result.get('evidence_count', 0)} evidence, {advanced_time:.2f}s")
            
        except Exception as e:
            print(f"   ❌ Advanced system failed: {str(e)}")
            results['advanced_result'] = {'error': str(e), 'evidence_count': 0, 'answer': ''}
            results['execution_times']['advanced'] = 999.0
        
        # Calculate metrics
        accuracy_metrics = self.evaluate_accuracy(query_info, results['simple_result'], results['advanced_result'])
        robustness_metrics = self.evaluate_robustness(query_info, results['simple_result'], results['advanced_result'])
        latency_metrics = self.evaluate_latency(results['execution_times']['simple'], results['execution_times']['advanced'])
        
        results['metrics'] = {
            **accuracy_metrics,
            **robustness_metrics,
            **latency_metrics
        }
        
        return results
    
    def run_full_benchmark(self) -> Dict[str, Any]:
        """Run complete benchmark suite"""
        print("🏁 STARTING COMPREHENSIVE RAG BENCHMARK")
        print("=" * 60)
        print(f"Testing {len(self.test_queries)} queries across multiple dimensions")
        print("=" * 60)
        
        all_results = []
        
        for i, query_info in enumerate(self.test_queries, 1):
            print(f"\n[{i}/{len(self.test_queries)}]", end="")
            result = self.run_single_comparison(query_info)
            all_results.append(result)
        
        # Calculate summary metrics
        summary = self.calculate_summary_metrics(all_results)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(summary)
        
        # Compile final results
        final_results = {
            'timestamp': datetime.now().isoformat(),
            'test_results': all_results,
            'summary_metrics': summary,
            'recommendations': recommendations
        }
        
        # Save results
        results_file = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(final_results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        return final_results
    
    def calculate_summary_metrics(self, all_results: List[Dict]) -> Dict[str, Any]:
        """Calculate overall summary metrics"""
        print(f"\n📊 CALCULATING SUMMARY METRICS")
        print("-" * 40)
        
        # Collect metrics by category
        accuracy_results = [r for r in all_results if r['query_info']['category'] == 'accuracy']
        robustness_results = [r for r in all_results if r['query_info']['category'] == 'robustness']
        latency_results = [r for r in all_results if r['query_info']['category'] == 'latency']
        
        summary = {}
        
        # ACCURACY SUMMARY
        if accuracy_results:
            theme_improvements = [r['metrics']['theme_coverage_improvement'] for r in accuracy_results]
            evidence_ratios = [r['metrics']['evidence_count_ratio'] for r in accuracy_results]
            
            summary['accuracy'] = {
                'avg_theme_coverage_improvement': statistics.mean(theme_improvements),
                'avg_evidence_ratio': statistics.mean(evidence_ratios),
                'queries_with_better_coverage': sum(1 for imp in theme_improvements if imp > 0),
                'total_accuracy_queries': len(accuracy_results)
            }
        
        # ROBUSTNESS SUMMARY
        if robustness_results:
            error_improvements = [r['metrics']['error_rate_improvement'] for r in robustness_results]
            meaningful_improvements = [r['metrics']['meaningful_response_improvement'] for r in robustness_results]
            
            summary['robustness'] = {
                'avg_error_rate_improvement': statistics.mean(error_improvements),
                'avg_meaningful_response_improvement': statistics.mean(meaningful_improvements),
                'queries_with_fewer_errors': sum(1 for imp in error_improvements if imp > 0),
                'total_robustness_queries': len(robustness_results)
            }
        
        # LATENCY SUMMARY
        all_simple_times = [r['execution_times']['simple'] for r in all_results if r['execution_times']['simple'] < 999]
        all_advanced_times = [r['execution_times']['advanced'] for r in all_results if r['execution_times']['advanced'] < 999]
        
        if all_simple_times and all_advanced_times:
            summary['latency'] = {
                'avg_simple_response_time': statistics.mean(all_simple_times),
                'avg_advanced_response_time': statistics.mean(all_advanced_times),
                'median_simple_response_time': statistics.median(all_simple_times),
                'median_advanced_response_time': statistics.median(all_advanced_times),
                'queries_under_10s': sum(1 for t in all_advanced_times if t < 10.0),
                'total_successful_queries': len(all_advanced_times)
            }
        
        # OVERALL SUMMARY
        successful_simple = sum(1 for r in all_results if r['simple_result'].get('evidence_count', 0) > 0)
        successful_advanced = sum(1 for r in all_results if r['advanced_result'].get('evidence_count', 0) > 0)
        
        summary['overall'] = {
            'total_queries_tested': len(all_results),
            'simple_success_rate': successful_simple / len(all_results),
            'advanced_success_rate': successful_advanced / len(all_results),
            'success_rate_improvement': (successful_advanced - successful_simple) / len(all_results)
        }
        
        return summary
    
    def generate_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on results"""
        recommendations = []
        
        # Accuracy recommendations
        if 'accuracy' in summary:
            acc = summary['accuracy']
            if acc['avg_theme_coverage_improvement'] > 0.2:
                recommendations.append("✅ STRONG ACCURACY IMPROVEMENT: Advanced system shows significant better theme coverage. Recommend deployment.")
            elif acc['avg_theme_coverage_improvement'] > 0.1:
                recommendations.append("⚠️ MODERATE ACCURACY IMPROVEMENT: Advanced system shows some improvement. Consider deployment with monitoring.")
            else:
                recommendations.append("❌ LIMITED ACCURACY IMPROVEMENT: Advanced system doesn't show clear accuracy benefits.")
        
        # Robustness recommendations
        if 'robustness' in summary:
            rob = summary['robustness']
            if rob['avg_error_rate_improvement'] > 0.1:
                recommendations.append("✅ IMPROVED ROBUSTNESS: Advanced system handles edge cases better.")
            if rob['avg_meaningful_response_improvement'] > 0.2:
                recommendations.append("✅ BETTER RESPONSE QUALITY: Advanced system provides more meaningful responses.")
        
        # Latency recommendations
        if 'latency' in summary:
            lat = summary['latency']
            if lat['avg_advanced_response_time'] < 5.0:
                recommendations.append("✅ ACCEPTABLE LATENCY: Response times are suitable for production.")
            elif lat['avg_advanced_response_time'] < 10.0:
                recommendations.append("⚠️ MODERATE LATENCY: Response times acceptable but monitor for user experience.")
            else:
                recommendations.append("❌ HIGH LATENCY: Response times may impact user experience. Consider optimization.")
        
        # Overall recommendation
        if 'overall' in summary:
            overall = summary['overall']
            if overall['success_rate_improvement'] > 0.2:
                recommendations.append("🚀 RECOMMENDATION: Deploy advanced system - shows clear improvements across metrics.")
            elif overall['success_rate_improvement'] > 0.1:
                recommendations.append("🤔 RECOMMENDATION: Consider gradual rollout of advanced system with A/B testing.")
            else:
                recommendations.append("🛑 RECOMMENDATION: Stick with simple system - advanced system doesn't justify complexity.")
        
        return recommendations
    
    def print_summary_report(self, results: Dict[str, Any]):
        """Print a formatted summary report"""
        print(f"\n{'='*70}")
        print("📋 BENCHMARK SUMMARY REPORT")
        print('='*70)
        
        summary = results['summary_metrics']
        
        if 'accuracy' in summary:
            acc = summary['accuracy']
            print(f"\n🎯 ACCURACY METRICS:")
            print(f"   Theme Coverage Improvement: {acc['avg_theme_coverage_improvement']:+.2f}")
            print(f"   Evidence Ratio: {acc['avg_evidence_ratio']:.2f}x")
            print(f"   Queries with Better Coverage: {acc['queries_with_better_coverage']}/{acc['total_accuracy_queries']}")
        
        if 'robustness' in summary:
            rob = summary['robustness']
            print(f"\n🛡️ ROBUSTNESS METRICS:")
            print(f"   Error Rate Improvement: {rob['avg_error_rate_improvement']:+.2f}")
            print(f"   Meaningful Response Improvement: {rob['avg_meaningful_response_improvement']:+.2f}")
            print(f"   Queries with Fewer Errors: {rob['queries_with_fewer_errors']}/{rob['total_robustness_queries']}")
        
        if 'latency' in summary:
            lat = summary['latency']
            print(f"\n⚡ LATENCY METRICS:")
            print(f"   Simple System Avg: {lat['avg_simple_response_time']:.2f}s")
            print(f"   Advanced System Avg: {lat['avg_advanced_response_time']:.2f}s")
            print(f"   Queries Under 10s: {lat['queries_under_10s']}/{lat['total_successful_queries']}")
        
        if 'overall' in summary:
            overall = summary['overall']
            print(f"\n📊 OVERALL PERFORMANCE:")
            print(f"   Simple Success Rate: {overall['simple_success_rate']:.1%}")
            print(f"   Advanced Success Rate: {overall['advanced_success_rate']:.1%}")
            print(f"   Success Rate Improvement: {overall['success_rate_improvement']:+.1%}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in results['recommendations']:
            print(f"   {rec}")
        
        print('='*70)

if __name__ == "__main__":
    print("🏁 RAG SYSTEM BENCHMARK COMPARISON")
    print("=" * 50)
    print("This will test both systems on accuracy, robustness, and latency")
    print("=" * 50)
    
    benchmark = RAGBenchmark()
    results = benchmark.run_full_benchmark()
    benchmark.print_summary_report(results)
    
    print(f"\n✅ Benchmark complete! Check the results file for detailed analysis.")