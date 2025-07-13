# 🔗 План интеграции фронтенда и бекенда для главного экрана

## Обзор

План интеграции главного экрана приложения с бекендом, основанный на уже реализованных паттернах в `LoginPage.tsx`.

## ✅ ОБНОВЛЕНО: Удален избыточный Main Screen API

**Проблема:** Main Screen API `/main/dashboard/{user_id}` просто дублировал данные из других endpoints.

**Решение:** Удален Main Screen API, используем отдельные специализированные endpoints:

- `/users/profile/{user_id}` - данные пользователя
- `/subscriptions/user/{user_id}` - подписки пользователя
- `/users/children/{parent_id}` - данные детей
- `/delivery-addresses/?user_id={userId}` - адреса доставки

**Преимущества:**

- Более RESTful подход
- Убирает дублирование кода
- Каждый endpoint отвечает за свою область
- Проще поддерживать и тестировать

## Анализ существующих паттернов

### ✅ Что уже реализовано в LoginPage.tsx:

- **HTTP клиент**: функция `apiRequest()` с обработкой ошибок
- **Типизация**: интерфейсы для API ответов (UserResponse, ChildResponse, etc.)
- **Состояние**: useState хуки для управления данными и загрузкой
- **Преобразование данных**: между форматами API и UI
- **Обработка ошибок**: централизованная через try/catch
- **Переменная окружения**: `REACT_APP_API_URL`

### 🔧 Паттерны которые нужно применить:

```typescript
// Существующий паттерн HTTP клиента
const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
  const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
  // ... обработка
};

// Существующий паттерн типизации
interface UserResponse {
  id: number;
  phone_number: string;
  name: string | null;
  role: string;
}

// Существующий паттерн состояний
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
```

## Шаг 1: Создание API типов для главного экрана

### Файл: `web/src/types/api.ts`

```typescript
// Дополнительные типы для главного экрана
export interface MainScreenData {
  user: {
    id: number;
    name: string;
    phone: string;
  };
  subscription: {
    active: boolean;
    plan_name: string | null;
    expires_at: string | null;
  } | null;
  children: Array<{
    id: number;
    name: string;
    age: number;
    gender: string;
  }>;
  next_delivery: any; // TODO: типизировать когда будет готово
  recommendations: any[]; // TODO: типизировать когда будет готово
}

export interface ToyBoxResponse {
  id: number;
  subscription_id: number;
  child_id: number;
  delivery_info_id: number | null;
  status: "PLANNED" | "ASSEMBLED" | "SHIPPED" | "DELIVERED" | "RETURNED";
  delivery_date: string | null;
  return_date: string | null;
  created_at: string;
  items: ToyBoxItemResponse[];
  reviews: ToyBoxReviewResponse[];
}

export interface ToyBoxItemResponse {
  id: number;
  toy_category_id: number;
  quantity: number;
}

export interface ToyBoxReviewResponse {
  id: number;
  user_id: number;
  rating: number;
  comment: string | null;
  created_at: string;
}

export interface ToyBoxReviewRequest {
  user_id: number;
  rating: number;
  comment?: string;
}
```

## Шаг 2: Создание хука для данных главного экрана

### Файл: `web/src/hooks/useMainScreenData.ts`

```typescript
import { useState, useEffect } from "react";
import {
  MainScreenData,
  ToyBoxResponse,
  ToyBoxReviewRequest,
} from "../types/api";

export const useMainScreenData = (userId: number | null) => {
  const [mainData, setMainData] = useState<MainScreenData | null>(null);
  const [currentToyBoxes, setCurrentToyBoxes] = useState<
    Map<number, ToyBoxResponse>
  >(new Map());
  const [nextToyBoxes, setNextToyBoxes] = useState<Map<number, ToyBoxResponse>>(
    new Map()
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Переиспользуем функцию apiRequest из LoginPage
  const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
    const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
    try {
      const response = await fetch(`${API_URL}${endpoint}`, {
        headers: { "Content-Type": "application/json" },
        ...options,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `API Error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  };

  const loadMainData = async () => {
    if (!userId) return;

    setIsLoading(true);
    setError(null);

    try {
      const data: MainScreenData = await apiRequest(
        `/main/dashboard/${userId}`
      );
      setMainData(data);

      // Загружаем наборы игрушек для каждого ребенка
      const currentBoxes = new Map<number, ToyBoxResponse>();
      const nextBoxes = new Map<number, ToyBoxResponse>();

      await Promise.all(
        data.children.map(async (child) => {
          try {
            const [currentBox, nextBox] = await Promise.all([
              apiRequest(`/toy-boxes/current/${child.id}`),
              apiRequest(`/toy-boxes/next/${child.id}`),
            ]);
            currentBoxes.set(child.id, currentBox);
            nextBoxes.set(child.id, nextBox);
          } catch (error) {
            console.error(
              `Failed to load toy boxes for child ${child.id}:`,
              error
            );
            // Не останавливаем загрузку из-за ошибки с одним ребенком
          }
        })
      );

      setCurrentToyBoxes(currentBoxes);
      setNextToyBoxes(nextBoxes);
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Не удалось загрузить данные"
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadMainData();
  }, [userId]);

  const submitReview = async (
    boxId: number,
    rating: number,
    comment: string
  ) => {
    if (!userId) return;

    setIsLoading(true);
    setError(null);

    try {
      const review: ToyBoxReviewRequest = {
        user_id: userId,
        rating,
        comment: comment || undefined,
      };

      await apiRequest(`/toy-boxes/${boxId}/review`, {
        method: "POST",
        body: JSON.stringify(review),
      });

      // Обновляем данные после отправки отзыва
      await loadMainData();
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Не удалось отправить отзыв"
      );
    } finally {
      setIsLoading(false);
    }
  };

  return {
    mainData,
    currentToyBoxes,
    nextToyBoxes,
    isLoading,
    error,
    reload: loadMainData,
    submitReview,
  };
};
```

## Шаг 3: Создание функций преобразования данных

### Файл: `web/src/utils/dataTransformers.ts`

```typescript
import { MainScreenData, ToyBoxResponse } from "../types/api";
import { UserData } from "../types";

// Преобразование данных API в формат фронтенда
export const transformMainScreenData = (
  apiData: MainScreenData,
  currentBoxes: Map<number, ToyBoxResponse>,
  nextBoxes: Map<number, ToyBoxResponse>
): UserData => {
  // Определяем статус подписки
  const getSubscriptionStatus = ():
    | "not_subscribed"
    | "just_subscribed"
    | "active" => {
    if (!apiData.subscription?.active) return "not_subscribed";

    // Проверяем, была ли подписка создана недавно (условная логика)
    if (apiData.subscription.expires_at) {
      const expiresAt = new Date(apiData.subscription.expires_at);
      const now = new Date();
      const diffHours =
        (now.getTime() - expiresAt.getTime()) / (1000 * 60 * 60);

      if (diffHours <= 2) return "just_subscribed";
    }

    return "active";
  };

  // Определяем статус следующего набора
  const getNextSetStatus = (): "not_determined" | "determined" => {
    // Если есть следующие наборы для детей, то определен
    return nextBoxes.size > 0 ? "determined" : "not_determined";
  };

  // Преобразуем детей
  const transformedChildren = apiData.children.map((child) => ({
    id: child.id,
    name: child.name,
    birthDate: new Date().toISOString(), // TODO: получить реальную дату из API
    gender: child.gender as "male" | "female",
    limitations: "none" as const, // TODO: получить из API
    comment: "",
    interests: [], // TODO: получить из API
    skills: [], // TODO: получить из API
    subscription: apiData.subscription?.active
      ? ("base" as const)
      : ("" as const), // TODO: определить тип подписки
  }));

  return {
    name: apiData.user.name,
    phone: apiData.user.phone,
    children: transformedChildren,
    deliveryAddress: "", // TODO: получить из API
    deliveryDate: "", // TODO: получить из API
    deliveryTime: "", // TODO: получить из API
    subscriptionStatus: getSubscriptionStatus(),
    nextSetStatus: getNextSetStatus(),
    subscriptionDate: apiData.subscription?.expires_at || undefined,
  };
};

// Преобразование данных набора игрушек
export const transformToyBoxToToys = (toyBox: ToyBoxResponse) => {
  return toyBox.items.map((item) => ({
    icon: getToyIcon(item.toy_category_id), // TODO: создать маппинг
    count: item.quantity,
    name: getToyName(item.toy_category_id), // TODO: создать маппинг
    color: getToyColor(item.toy_category_id), // TODO: создать маппинг
  }));
};

// Вспомогательные функции (TODO: получать с бекенда)
// TODO: Доработать ToyBoxItemResponse чтобы включать category_name и category_icon с бекенда
// Сейчас в ToyBoxItemResponse только toy_category_id, а нужна полная информация как в NextBoxItemResponse
const getToyIcon = (categoryId: number): string => {
  // Временная реализация до доработки API
  const icons = ["🔧", "🎨", "🧸", "🧠", "🎪"];
  return icons[categoryId % icons.length];
};

const getToyName = (categoryId: number): string => {
  // Временная реализация до доработки API
  const names = [
    "Конструктор",
    "Творческий набор",
    "Мягкая игрушка",
    "Головоломка",
    "Игра",
  ];
  return names[categoryId % names.length];
};

const getToyColor = (categoryId: number): string => {
  // Временная реализация
  const colors = ["#F8CAAF", "#D4E8C0", "#FFD8BE", "#F6E592", "#E8D3F0"];
  return colors[categoryId % colors.length];
};
```

## Шаг 4: Обновление KidsAppInterface.tsx

### Изменения в компоненте:

```typescript
// Добавить импорты
import { useMainScreenData } from "../hooks/useMainScreenData";
import {
  transformMainScreenData,
  transformToyBoxToToys,
} from "../utils/dataTransformers";

// Изменить интерфейс пропсов
interface KidsAppInterfaceProps {
  userId: number; // вместо userData
}

// В компоненте заменить логику
export const KidsAppInterface: React.FC<KidsAppInterfaceProps> = ({
  userId,
}) => {
  // Заменить useState на хук
  const {
    mainData,
    currentToyBoxes,
    nextToyBoxes,
    isLoading,
    error,
    reload,
    submitReview,
  } = useMainScreenData(userId);

  // Преобразовать данные
  const userData = mainData
    ? transformMainScreenData(mainData, currentToyBoxes, nextToyBoxes)
    : null;

  // Добавить обработку загрузки и ошибок
  if (isLoading && !userData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-600">Загружаем данные...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={reload}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  if (!userData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-600">Нет данных для отображения</p>
      </div>
    );
  }

  // Обновить функцию обработки отзывов
  const handleStarClick = (starIndex: number): void => {
    setRating(starIndex + 1);
    setShowFeedback(true);
  };

  const handleFeedbackSubmit = async (rating: number, comment: string) => {
    // Найти ID текущего набора (логика зависит от UI)
    const currentChild = userData.children[0]; // Упрощение для примера
    const currentBox = currentToyBoxes.get(currentChild.id);

    if (currentBox) {
      await submitReview(currentBox.id, rating, comment);
    }
  };

  // Обновить функции получения игрушек
  const getCurrentToys = () => {
    const currentChild = userData.children[0]; // Упрощение для примера
    const currentBox = currentToyBoxes.get(currentChild.id);

    if (currentBox) {
      return transformToyBoxToToys(currentBox);
    }

    // Fallback на существующую логику
    return getExistingCurrentToys();
  };

  const getNextToys = () => {
    const currentChild = userData.children[0]; // Упрощение для примера
    const nextBox = nextToyBoxes.get(currentChild.id);

    if (nextBox) {
      return transformToyBoxToToys(nextBox);
    }

    // Fallback на существующую логику
    return getExistingNextToys();
  };

  // Остальная логика остается прежней...
};
```

## Шаг 5: Обновление App.tsx

### Изменения в главном компоненте:

```typescript
// Обновить состояние для хранения userId
const [userId, setUserId] = useState<number | null>(null);

// Обновить функцию навигации
const handleNavigateToKidsPage = (data: UserData, userId: number) => {
  setUserId(userId);
  setCurrentPage("kids");
};

// Обновить рендер
if (currentPage === "kids" && userId) {
  return (
    <div>
      <div className="fixed top-4 left-4 z-50">
        <button
          onClick={handleBackToDemo}
          className="bg-gray-800 text-white px-4 py-2 rounded-lg text-sm font-medium"
        >
          ← Назад к демо
        </button>
      </div>
      <KidsAppInterface userId={userId} />
    </div>
  );
}
```

## Приоритеты реализации

### 🔥 Критично (неделя 1):

1. ✅ Создать API типы
2. ✅ Создать хук useMainScreenData
3. ✅ Обновить KidsAppInterface для загрузки данных

### 🔴 Важно (неделя 2):

1. ⚠️ Доработать преобразование данных
2. ⚠️ Интегрировать отзывы
3. ⚠️ Обработать состояния загрузки

### 🟡 Желательно (неделя 3):

1. ⭐ Добавить кэширование
2. ⭐ Добавить оптимистичные обновления
3. ⭐ Улучшить обработку ошибок

## Особенности реализации

### Переиспользование паттернов:

- Используем те же подходы что в `LoginPage.tsx`
- Вызываем `apiRequest` напрямую без промежуточного слоя
- Сохраняем структуру типов и обработки ошибок

### Обратная совместимость:

- Сохраняем существующие интерфейсы (`UserData`)
- Добавляем слой преобразования данных
- Поддерживаем fallback на моковые данные

### Постепенная миграция:

- Можно внедрять по частям
- Сначала основные данные, потом детали
- Тестировать каждый этап отдельно

## Тестирование

### Ручное тестирование:

1. Проверить загрузку данных главного экрана
2. Проверить различные состояния пользователя
3. Проверить отправку отзывов
4. Проверить обработку ошибок

### Переменные окружения:

```bash
# В .env файле
REACT_APP_API_URL=http://localhost:8000
```

### Отладка:

- Использовать console.log в функциях API
- Проверять Network tab в DevTools
- Тестировать с разными пользователями
