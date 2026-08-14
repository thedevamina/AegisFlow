<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class MLService
{
    protected string $baseUrl;
    protected int $timeout;

    public function __construct()
    {
        $this->baseUrl = rtrim(config('services.ml.url'), '/');
        $this->timeout = (int) config('services.ml.timeout', 15);
    }

    public function predict(array $prPayload): array
    {
        $response = Http::baseUrl($this->baseUrl)
            ->timeout($this->timeout)
            ->retry(2, 500)
            ->post('/predict', $prPayload);

        if ($response->failed()) {
            Log::error('ML service prediction failed', [
                'status' => $response->status(),
                'body' => $response->body(),
            ]);
            $response->throw();
        }

        return $response->json();
    }

    public function healthy(): bool
    {
        try {
            return Http::baseUrl($this->baseUrl)->timeout(5)->get('/health')->successful();
        } catch (\Throwable $e) {
            return false;
        }
    }
}