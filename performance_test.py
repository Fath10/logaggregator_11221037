
import asyncio
import httpx
import time
from datetime import datetime, timezone
import random
import json
from typing import List, Dict

BASE_URL = "http://localhost:8080"
TOTAL_EVENTS = 5000  # Minimum required
DUPLICATION_RATE = 0.25  # 25% duplication (exceeds 20% requirement)
BATCH_SIZE = 100
CONCURRENT_REQUESTS = 10
TOPICS = ["user.login", "user.logout", "order.created", "order.paid", "system.alert"]

class PerformanceTest:
    def __init__(self):
        self.total_sent = 0
        self.total_accepted = 0
        self.total_duplicates = 0
        self.response_times = []
        self.errors = 0
        self.start_time = None
        self.end_time = None
        
    def generate_event(self, event_id: str, is_duplicate: bool = False) -> Dict:

        return {
            "topic": random.choice(TOPICS),
            "event_id": event_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "performance-test",
            "payload": {
                "test_id": event_id,
                "is_duplicate": is_duplicate,
                "random_data": random.randint(1, 1000)
            }
        }
    
    def generate_event_batch(self, start_idx: int, batch_size: int, duplicate_ids: set) -> List[Dict]:

        events = []
        for i in range(start_idx, start_idx + batch_size):
            event_id = f"perf-test-{i}"
            is_duplicate = event_id in duplicate_ids
            events.append(self.generate_event(event_id, is_duplicate))
        return events
    
    async def publish_batch(self, client: httpx.AsyncClient, events: List[Dict]) -> Dict:

        start = time.time()
        try:
            response = await client.post(
                f"{BASE_URL}/publish",
                json={"events": events},
                timeout=30.0
            )
            response.raise_for_status()
            elapsed = time.time() - start
            self.response_times.append(elapsed)
            return response.json()
        except Exception as e:
            self.errors += 1
            print(f"❌ Error: {e}")
            return {"received": 0, "accepted": 0, "duplicates": 0}
    
    async def check_health(self, client: httpx.AsyncClient) -> Dict:

        try:
            response = await client.get(f"{BASE_URL}/health", timeout=5.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_stats(self, client: httpx.AsyncClient) -> Dict:

        try:
            response = await client.get(f"{BASE_URL}/stats", timeout=5.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def run_test(self):

        print("=" * 80)
        print("🚀 UTS LOG AGGREGATOR - PERFORMANCE TEST")
        print("=" * 80)
        print(f"📊 Test Configuration:")
        print(f"   • Total Events: {TOTAL_EVENTS:,}")
        print(f"   • Duplication Rate: {DUPLICATION_RATE*100:.1f}%")
        print(f"   • Expected Duplicates: {int(TOTAL_EVENTS * DUPLICATION_RATE):,}")
        print(f"   • Batch Size: {BATCH_SIZE}")
        print(f"   • Concurrent Requests: {CONCURRENT_REQUESTS}")
        print(f"   • Topics: {len(TOPICS)}")
        print("=" * 80)
        print()

        print("📝 Generating event IDs with duplication pattern...")
        unique_event_count = int(TOTAL_EVENTS * (1 - DUPLICATION_RATE))
        duplicate_event_count = TOTAL_EVENTS - unique_event_count

        unique_ids = [f"perf-test-{i}" for i in range(unique_event_count)]

        duplicate_pool = random.sample(unique_ids, min(duplicate_event_count, len(unique_ids)))
        all_event_ids = unique_ids + duplicate_pool
        random.shuffle(all_event_ids)
        
        duplicate_ids = set(duplicate_pool)
        
        print(f"   ✅ Generated {len(unique_ids):,} unique IDs")
        print(f"   ✅ Generated {len(duplicate_pool):,} duplicate IDs")
        print(f"   ✅ Total IDs to process: {len(all_event_ids):,}")
        print()

        print("🏥 Checking initial system health...")
        async with httpx.AsyncClient() as client:
            health = await self.check_health(client)
            print(f"   Status: {health.get('status', 'unknown')}")
            print(f"   Consumer Running: {health.get('consumer_running', False)}")
            print(f"   Queue Size: {health.get('queue_size', 0)}")
        print()

        print("⏱️  Starting performance test...")
        self.start_time = time.time()
        
        async with httpx.AsyncClient() as client:

            batches = []
            for i in range(0, len(all_event_ids), BATCH_SIZE):
                batch_ids = all_event_ids[i:i + BATCH_SIZE]
                events = [self.generate_event(eid, eid in duplicate_ids) for eid in batch_ids]
                batches.append(events)
            
            print(f"📦 Created {len(batches)} batches")
            print()

            total_batches = len(batches)
            completed_batches = 0
            
            for i in range(0, total_batches, CONCURRENT_REQUESTS):
                batch_group = batches[i:i + CONCURRENT_REQUESTS]
                tasks = [self.publish_batch(client, batch) for batch in batch_group]
                results = await asyncio.gather(*tasks)
                
                for result in results:
                    self.total_sent += result.get("received", 0)
                    self.total_accepted += result.get("accepted", 0)
                    self.total_duplicates += result.get("duplicates", 0)
                
                completed_batches += len(batch_group)
                progress = (completed_batches / total_batches) * 100

                if completed_batches % max(1, total_batches // 10) == 0 or completed_batches == total_batches:
                    elapsed = time.time() - self.start_time
                    rate = self.total_sent / elapsed if elapsed > 0 else 0
                    avg_response = sum(self.response_times) / len(self.response_times) if self.response_times else 0
                    
                    print(f"📈 Progress: {progress:5.1f}% | "
                          f"Sent: {self.total_sent:,} | "
                          f"Rate: {rate:,.0f} events/s | "
                          f"Avg Response: {avg_response*1000:.0f}ms")

                if completed_batches % max(1, total_batches // 5) == 0:
                    health = await self.check_health(client)
                    queue_size = health.get('queue_size', 0)
                    if queue_size > BATCH_SIZE * 2:
                        print(f"   ⚠️  Queue building up: {queue_size} events")
            
            self.end_time = time.time()

            print()
            print("⏳ Waiting for consumer to process all events...")
            await asyncio.sleep(5)

            print()
            print("📊 Fetching final statistics...")
            stats = await self.get_stats(client)
            health = await self.check_health(client)

        self.print_results(stats, health)
    
    def print_results(self, stats: Dict, health: Dict):

        duration = self.end_time - self.start_time
        avg_response = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        min_response = min(self.response_times) if self.response_times else 0
        max_response = max(self.response_times) if self.response_times else 0
        p95_response = sorted(self.response_times)[int(len(self.response_times) * 0.95)] if self.response_times else 0
        
        print()
        print("=" * 80)
        print("📊 PERFORMANCE TEST RESULTS")
        print("=" * 80)
        print()
        
        print("📤 Sending Statistics:")
        print(f"   • Total Events Sent: {self.total_sent:,}")
        print(f"   • Total Accepted: {self.total_accepted:,}")
        print(f"   • Total Duplicates Detected: {self.total_duplicates:,}")
        print(f"   • Errors: {self.errors}")
        print(f"   • Duplication Rate: {(self.total_duplicates/self.total_sent*100) if self.total_sent > 0 else 0:.2f}%")
        print()
        
        print("⚡ Performance Metrics:")
        print(f"   • Test Duration: {duration:.2f}s")
        print(f"   • Throughput: {self.total_sent/duration:,.0f} events/s")
        print(f"   • Avg Response Time: {avg_response*1000:.2f}ms")
        print(f"   • Min Response Time: {min_response*1000:.2f}ms")
        print(f"   • Max Response Time: {max_response*1000:.2f}ms")
        print(f"   • P95 Response Time: {p95_response*1000:.2f}ms")
        print()
        
        print("📊 System Statistics (from /stats endpoint):")
        print(f"   • Total Received: {stats.get('received', 0):,}")
        print(f"   • Unique Processed: {stats.get('unique_processed', 0):,}")
        print(f"   • Duplicates Dropped: {stats.get('duplicate_dropped', 0):,}")
        print(f"   • Active Topics: {len(stats.get('topics', []))}")
        print(f"   • Uptime: {stats.get('uptime_human', 'N/A')}")
        print()
        
        print("🏥 Final System Health:")
        print(f"   • Status: {health.get('status', 'unknown')}")
        print(f"   • Consumer Running: {health.get('consumer_running', False)}")
        print(f"   • Queue Size: {health.get('queue_size', 0)}")
        print()

        print("✅ TEST VALIDATION:")
        print()

        events_ok = self.total_sent >= TOTAL_EVENTS
        print(f"   {'✅' if events_ok else '❌'} Event Count: {self.total_sent:,} >= {TOTAL_EVENTS:,} (Required)")

        actual_dup_rate = (self.total_duplicates / self.total_sent * 100) if self.total_sent > 0 else 0
        required_dup_rate = 20.0
        dup_ok = actual_dup_rate >= required_dup_rate
        print(f"   {'✅' if dup_ok else '❌'} Duplication Rate: {actual_dup_rate:.2f}% >= {required_dup_rate}% (Required)")

        responsive_ok = avg_response < 1.0
        print(f"   {'✅' if responsive_ok else '❌'} Responsiveness: Avg {avg_response*1000:.0f}ms < 1000ms (Target)")

        no_errors = self.errors == 0
        print(f"   {'✅' if no_errors else '❌'} Error Rate: {self.errors} errors")

        healthy = health.get('status') == 'healthy'
        print(f"   {'✅' if healthy else '❌'} System Health: {health.get('status', 'unknown')}")

        queue_ok = health.get('queue_size', 0) < 1000
        print(f"   {'✅' if queue_ok else '❌'} Queue Size: {health.get('queue_size', 0)} < 1000")
        
        print()
        all_passed = events_ok and dup_ok and responsive_ok and no_errors and healthy and queue_ok
        
        if all_passed:
            print("🎉 " + "=" * 76)
            print("🎉 ALL TESTS PASSED! System meets performance requirements.")
            print("🎉 " + "=" * 76)
        else:
            print("⚠️  " + "=" * 76)
            print("⚠️  Some tests failed. Review results above.")
            print("⚠️  " + "=" * 76)
        
        print()
        print("=" * 80)

async def main():

    test = PerformanceTest()
    
    try:
        await test.run_test()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print()
    print("Starting performance test in 3 seconds...")
    print("Make sure the service is running on http://localhost:8080")
    print()
    time.sleep(3)
    
    asyncio.run(main())
